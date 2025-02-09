from abc import ABC, abstractmethod
import base64
from typing import Dict, List, Tuple, Union, Optional
import os
from pathlib import Path
import fitz  # PyMuPDF
import hashlib
import math
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from dataclasses import dataclass

from openai import OpenAI

from llm.factory import LLMFactory, LLMType

from pypdf import PdfReader
from PIL import Image
import io

@dataclass
class PageImage:
    """Represents a PDF page converted to an image"""
    page_number: int
    image_bytes: bytes

@dataclass
class PDFImage:
    """Represents an image extracted from a PDF"""
    name: str
    image_bytes: bytes
    page_number: int
    size: Tuple[int, int]  # (width, height)

@dataclass
class TOCEntry:
    """Represents a table of contents entry"""
    title: str
    level: int
    page_number: int

@dataclass
class Page:
    """Represents a processed PDF page with its content and metadata"""
    page_number: int
    content: str
    page_image: PageImage  # The full page converted to image
    images: List[PDFImage]  # List of images found on the page
    titles: List[TOCEntry]  # List of titles/headers found on the page



class BaseConverter(ABC):
    def __init__(self, 
                 doc_path: str, 
                 api_key: str, 
                 judge_api_key: str,
                 llm_type: str = "gpt4-vision",
                 chunk_size: int = 10, 
                 max_chunks: int = 10):
        """Initialize the converter."""
        self.doc_path = doc_path
        self.api_key = api_key
        self.judge_api_key = judge_api_key
        self.llm_type = llm_type
        self.chunk_size = chunk_size
        self.max_chunks = max_chunks
        self.pages: List[Page] = []
        self.llm_client = LLMFactory.create_client(llm_type, api_key)
        self.llm_judge = LLMFactory.create_client(LLMType.GEMINI_FLASH_2, judge_api_key)

    def convert(self) -> str:
        """Main conversion pipeline"""
        # Convert PDF pages to images and extract embedded images
        page_images = self.pdf_to_images()

        self.pages = [
            Page(
                page_number=page_img.page_number,
                content="",  # Will be populated during processing
                page_image=page_img,
                images=[],   # Will be populated by _extract_images
                titles=[]    # Will be populated during processing
            )
            for page_img in page_images
        ]

        # Extract images from PDF   
        self._extract_images()
        
        # Split pages into chunks for parallel processing
        chunks = self._split_pages(self.pages)
        
        # Process chunks in parallel
        self._process_chunks_parallel(chunks)
        
        # Merge all content
        final_text = self._merge_content()
        
        return final_text
    
    def pdf_to_images(self) -> List[PageImage]:
        """Convert PDF pages to images
        
        Returns:
            List[PageImage]: List of PageImage objects containing page number and image bytes
        """
        page_images: List[PageImage] = []
        
        with fitz.open(self.doc_path) as pdf_document:
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Get the page's pixmap with zoom factor of 2
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                
                # Convert pixmap to PNG bytes and store with page number
                image_bytes = pix.tobytes("png")
                page_images.append(PageImage(page_number=page_num, image_bytes=image_bytes))
        
        # self.pages = [
        #     Page(
        #         page_number=page_img.page_number,
        #         content="",  # Will be populated during processing
        #         page_image=page_img,
        #         images=[],   # Will be populated by _extract_images
        #         titles=[]    # Will be populated during processing
        #     )
        #     for page_img in page_images
        # ]

        return page_images
    
    def _extract_images(self):
        """Extract images from PDF"""
        reader = PdfReader(self.doc_path)
        
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            page_images: List[PDFImage] = []
            
            try:
                # Extract regular images
                for image_file_object in page.images:
                    image = self._process_image_data(image_file_object.data, page_num)
                    if image:
                        page_images.append(image)
                
                # Extract images from annotations
                if "/Annots" in page:
                    for annot in page["/Annots"]:
                        try:
                            annot_obj = annot.get_object()
                            if "/AP" in annot_obj:
                                ap_dict = annot_obj["/AP"]
                                if "/N" in ap_dict:
                                    n_obj = ap_dict["/N"]
                                    if "/Resources" in n_obj and "/XObject" in n_obj["/Resources"]:
                                        for xobj in n_obj["/Resources"]["/XObject"].values():
                                            try:
                                                image = xobj.decode_as_image()
                                                if image:
                                                    output = io.BytesIO()
                                                    image.save(output, format='PNG', optimize=True)
                                                    processed_image = self._process_image_data(output.getvalue(), page_num)
                                                    if processed_image:
                                                        page_images.append(processed_image)
                                            except Exception as e:
                                                print(f"Warning: Failed to decode annotation image on page {page_num}: {str(e)}")
                        except Exception as e:
                            print(f"Warning: Failed to process annotation on page {page_num}: {str(e)}")
                
                # Update the page's images if it exists
                for page_obj in self.pages:
                    if page_obj.page_number == page_num:
                        page_obj.images = page_images
                        break
                
            except Exception as e:
                print(f"Warning: Failed to process images on page {page_num}: {str(e)}")
    
    def _process_image_data(self, image_bytes: bytes, page_num: int) -> Optional[PDFImage]:
        """Process and validate image data"""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            
            # Skip tiny images
            if img.size[0] < 10 or img.size[1] < 10:
                return None
                
            # Skip solid color images
            extrema = img.convert('L').getextrema()
            if extrema[0] == extrema[1] or (extrema[1] - extrema[0] < 5):
                return None
            
            # Convert to PNG format
            output = io.BytesIO()
            img.save(output, format='PNG', optimize=True)
            image_bytes = output.getvalue()
            
            # Generate unique filename
            image_hash = hashlib.md5(image_bytes).hexdigest()[:12]
            image_name = f"image_{page_num}_{image_hash}.png"
            
            return PDFImage(
                name=image_name,
                image_bytes=image_bytes,
                page_number=page_num,
                size=img.size
            )
            
        except Exception as e:
            print(f"Warning: Image processing failed on page {page_num}: {str(e)}")
            return None
    
    def _process_chunks_parallel(self, chunks: List[List[Page]]) -> None:
        """Process chunks in parallel using multiple threads."""
        def process_chunk(chunk: List[Page]) -> List[Page]:
            print(f"Processing chunk of size {len(chunk)}")
            return [
                Page(
                    page_number=page.page_number,
                    content=self._process_page(page),
                    page_image=page.page_image,
                    images=[],  # Will be populated by _extract_images
                    titles=[]   # Should be extracted from content
                )
                for page in chunk
            ]
        
        with ThreadPoolExecutor() as executor:
            future_to_chunk = {
                executor.submit(process_chunk, chunk): i 
                for i, chunk in enumerate(chunks)
            }
            
            for future in as_completed(future_to_chunk):
                try:
                    def find_page_index(page_number: int) -> int:
                        return next((i for i, p in enumerate(self.pages) if p.page_number == page_number), None)
                    # self.pages[find_page_index(future.result()[0].page_number)] = future.result()[0]
                    for page in future.result():
                        self.pages[find_page_index(page.page_number)] = page
                    # self.pages.extend(future.result())
                except Exception as e:
                    print(f"Error processing chunk: {str(e)}")
        
        # Sort pages by page number
        self.pages.sort(key=lambda p: p.page_number)
    
    @abstractmethod
    def _process_page(self, page: Page) -> str:
        """Process a single page using LLM"""
        pass
    
    @abstractmethod
    def _merge_content(self) -> str:
        """Merge all processed content into final document"""
        pass

    def _rewrite_page(self, content: str) -> Optional[str]:
        """
        Extract markdown content from XML tags.
        
        Args:
            content (str): Raw content with XML tags
            
        Returns:
            Optional[str]: Extracted markdown content or None if no valid content found
        """
        try:
            # Find content between <markdown> tags using regex
            pattern = r'<task_two>(.*?)</task_two>'
            # Use re.DOTALL to match across multiple lines
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                # Extract and clean the content
                markdown_content = match.group(1)
                # Remove leading/trailing whitespace while preserving internal formatting
                markdown_content = markdown_content.strip()
                return markdown_content
            
            print("Warning: No markdown tags found in content")
            return None
            
        except Exception as e:
            print(f"Error extracting markdown content: {str(e)}")
            return None

    def _split_pages(self, pages: List[Page]) -> List[List[Page]]:
        """Split pages into chunks for parallel processing
        
        Args:
            page_images (List[PageImage]): List of all page images
            
        Returns:
            List[List[PageImage]]: List of page image chunks
        """
        # Calculate number of chunks needed
        total_pages = len(pages)
        num_chunks = min(math.ceil(total_pages / self.chunk_size), self.max_chunks)
        
        # Calculate actual chunk size based on number of chunks
        chunk_size = math.ceil(total_pages / num_chunks)
        
        # Split pages into chunks
        chunks = [
            pages[i:i + chunk_size] 
            for i in range(0, total_pages, chunk_size)
        ]
        
        return chunks

    def _extract_toc(self):
        """Extract table of contents and associate titles with pages"""
        reader = PdfReader(self.doc_path)
        def extract_toc(outlines, level=0):
            for item in outlines:
                if isinstance(item, list):
                    extract_toc(item, level + 1)
                else:
                    page_index = next((i for i, page in enumerate(self.pages) if page.page_number == reader.get_destination_page_number(item) - 1), None)
                    self.pages[page_index].titles = self.pages[page_index].titles + [
                        TOCEntry(
                            title=item.title,
                            level=level,
                            page_number=reader.get_destination_page_number(item)
                        )
                    ]
                    # print(str(reader.get_destination_page_number(item)) + "  " * level + "- " + item.title)
        outlines = reader.outline
        extract_toc(outlines)
    # def _extract_toc(self) -> Dict[int, List[TOCEntry]]:
    #     """Extract table of contents and associate titles with pages
        
    #     Returns:
    #         Dict[int, List[TOCEntry]]: Dictionary mapping page numbers to their TOC entries
    #     """
    #     reader = PdfReader(self.doc_path)
        
    #     # Initialize titles for all pages
    #     page_titles: Dict[int, List[TOCEntry]] = {i: [] for i in range(len(reader.pages))}
        
    #     def process_outline(outlines, level=0):
    #         """Recursively process outline items"""
    #         for item in outlines:
    #             if isinstance(item, list):
    #                 process_outline(item, level + 1)
    #             else:
    #                 try:
    #                     page_num = reader.get_destination_page_number(item)
    #                     if page_num is not None:
    #                         # Create TOCEntry and add to page's entries
    #                         toc_entry = TOCEntry(
    #                             title=item.title,
    #                             level=level,
    #                             page_number=page_num
    #                         )
    #                         page_titles[page_num].append(toc_entry)
    #                 except Exception as e:
    #                     print(f"Warning: Failed to process TOC item {item.title}: {str(e)}")
        
    #     # Process outline if it exists
    #     if reader.outline:
    #         try:
    #             process_outline(reader.outline)
    #         except Exception as e:
    #             print(f"Warning: Failed to process table of contents: {str(e)}")
        
    #     # Update pages with their titles
    #     for page in self.pages:
    #         page.titles = [
    #             entry.title 
    #             for entry in page_titles.get(page.page_number, [])
    #         ]
        
    #     return page_titles
