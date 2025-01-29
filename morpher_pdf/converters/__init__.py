from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Union
import os
from pathlib import Path
import fitz  # PyMuPDF
import hashlib

class BaseConverter(ABC):
    def __init__(self, doc_path: str, openai_key: str):
        self.doc_path = doc_path
        self.openai_key = openai_key
        self.images_by_page: Dict[int, List[Tuple[str, bytes]]] = {}
        self.page_contents: List[str] = []
        
    def convert(self) -> Tuple[str, List[str]]:
        """Main conversion pipeline"""
        # Load PDF and extract images
        self._extract_images()
        
        # Convert PDF pages to images
        page_images = self._pdf_to_images()
        
        # Split pages into chunks for parallel processing
        chunks = self._split_pages(page_images)
        
        # Process chunks in parallel
        self.page_contents = self._process_chunks_parallel(chunks)
        
        # Merge all images into a single array
        all_images = self._merge_images()
        
        # Merge all text content
        final_text = self._merge_content()
        
        return final_text, all_images
    
    @abstractmethod
    def _process_chunk(self, chunk: bytes) -> str:
        """Process a single chunk using LLM"""
        pass
    
    def _extract_images(self):
        """Extract images from PDF and store in page map"""
        # Open the PDF using context manager
        with fitz.open(self.doc_path) as pdf_document:
            # Iterate through pages
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                image_list = page.get_images()
                
                # Initialize empty list for current page
                self.images_by_page[page_num] = []
                
                # Iterate through images on the page
                for img_idx, img in enumerate(image_list):
                    # Get image data
                    xref = img[0]  # Cross-reference number
                    base_image = pdf_document.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Generate unique filename using hash of image content
                    image_hash = hashlib.md5(image_bytes).hexdigest()[:12]
                    image_ext = base_image["ext"]  # Get image extension (jpeg, png, etc.)
                    image_name = f"image_{page_num}_{image_hash}.{image_ext}"
                    
                    # Store image name and content in the page map
                    self.images_by_page[page_num].append((image_name, image_bytes))
    
    def _pdf_to_images(self) -> List[bytes]:
        """Convert PDF pages to images"""
        page_images = []
        
        # Open PDF using context manager
        with fitz.open(self.doc_path) as pdf_document:
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Get the page's pixmap (image representation)
                # Using a zoom factor of 2 for better quality
                # Using RGB color space (no alpha channel)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                
                # Convert pixmap to PNG bytes
                image_bytes = pix.tobytes("png")
                page_images.append(image_bytes)
        
        return page_images
    
    def _split_pages(self, pages: List[bytes]) -> List[bytes]:
        """Split pages into processable chunks"""
        pass
    
    def _process_chunks_parallel(self, chunks: List[bytes]) -> List[str]:
        """Process chunks in parallel using LLM"""
        pass
    
    def _merge_images(self) -> List[str]:
        """Merge all images into a single array"""
        pass
    
    def _merge_content(self) -> str:
        """Merge all processed content into final document"""
        pass
