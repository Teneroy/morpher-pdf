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

from openai import OpenAI

from llm.factory import LLMFactory

class BaseConverter(ABC):
    def __init__(self, 
                 doc_path: str, 
                 api_key: str, 
                 llm_type: str = "gpt4-vision",
                 chunk_size: int = 10, 
                 max_chunks: int = 10):
        """
        Initialize the converter.
        
        Args:
            doc_path (str): Path to the document
            api_key (str): API key for the LLM service
            llm_type (str): Type of LLM to use (default: "gpt4-vision")
            chunk_size (int): Number of pages per chunk
            max_chunks (int): Maximum number of chunks to process
        """
        self.doc_path = doc_path
        self.api_key = api_key
        self.llm_type = llm_type
        self.chunk_size = chunk_size
        self.max_chunks = max_chunks
        self.images_by_page: Dict[int, List[Tuple[str, bytes]]] = {}
        self.page_contents: List[str] = []
        self.llm_client = LLMFactory.create_client(llm_type, api_key)
        
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
    def _process_page(self, page: bytes) -> str:
        """Process a single page using LLM"""
        pass
    
    def _extract_images(self):
        """Extract images from PDF and store in page map"""
        # Open the PDF using context manager
        with fitz.open(self.doc_path) as pdf_document:
            # Iterate through pages
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Initialize empty list for current page
                self.images_by_page[page_num] = []
                
                try:
                    # Method 1: Extract embedded images
                    self._extract_embedded_images(pdf_document, page, page_num)
                    
                    # Method 2: Extract vector graphics and other content as images
                    self._extract_page_regions(page, page_num)
                except Exception as e:
                    print(f"Warning: Error processing page {page_num}: {str(e)}")
                    continue
    
    def _extract_embedded_images(self, pdf_document, page, page_num):
        """Extract embedded raster images from the page"""
        # Try different methods to get images
        try:
            # Method 1: Using get_images()
            image_list = page.get_images()
            
            # If no images found, try alternative method
            if not image_list:
                # Method 2: Using get_image_info()
                image_list = [(img["xref"], img) for img in page.get_image_info()]
            
            for img_idx, img in enumerate(image_list):
                try:
                    # Handle both tuple format from get_images() and dict format from get_image_info()
                    xref = img[0] if isinstance(img, tuple) else img["xref"]
                    
                    # Extract image
                    base_image = pdf_document.extract_image(xref)
                    
                    if base_image is None:
                        continue
                        
                    image_bytes = base_image["image"]
                    
                    # Try to handle different image formats and masks
                    try:
                        from PIL import Image
                        import io
                        
                        # Convert to PIL Image for processing
                        img = Image.open(io.BytesIO(image_bytes))
                        
                        # Handle SMask if present
                        if "smask" in base_image:
                            smask_bytes = base_image["smask"]
                            mask = Image.open(io.BytesIO(smask_bytes))
                            
                            # Convert images to appropriate modes
                            if img.mode not in ['RGBA', 'LA']:
                                img = img.convert('RGBA')
                            if mask.mode != 'L':
                                mask = mask.convert('L')
                            
                            # Apply mask
                            img.putalpha(mask)
                        
                        # Basic image validation
                        if img.size[0] < 10 or img.size[1] < 10:  # Skip tiny images
                            continue
                            
                        # Skip solid color images but with more lenient threshold
                        extrema = img.convert('L').getextrema()
                        if extrema[0] == extrema[1] or (extrema[1] - extrema[0] < 5):
                            continue
                        
                        # Convert back to bytes
                        output = io.BytesIO()
                        img.save(output, format='PNG', optimize=True)
                        image_bytes = output.getvalue()
                        base_image["ext"] = "png"
                        
                    except Exception as e:
                        print(f"Warning: Image processing failed on page {page_num}: {str(e)}")
                        # If PIL processing fails, use original image
                        pass
                    
                    # Generate unique filename
                    image_hash = hashlib.md5(image_bytes).hexdigest()[:12]
                    image_ext = base_image.get("ext", "png")
                    image_name = f"image_{page_num}_{image_hash}.{image_ext}"
                    
                    # Store image
                    self.images_by_page[page_num].append((image_name, image_bytes))
                    
                except Exception as e:
                    print(f"Warning: Failed to extract image {img_idx} on page {page_num}: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"Warning: Failed to process images on page {page_num}: {str(e)}")
    
    def _extract_page_regions(self, page, page_num):
        """Extract vector graphics and other content as images"""
        try:
            # Get drawings and graphics from the page
            paths = page.get_drawings()
            if not paths:  # Skip if no vector graphics found
                return
                
            # Get page dimensions
            rect = page.rect
            
            from PIL import Image
            import io
            import numpy as np
            
            def is_likely_axis(path):
                """Check if a drawing path might be part of an axis"""
                # Check for straight lines
                if 'items' in path:
                    items = path['items']
                    if items:
                        # Check if it's a line
                        if path.get('type') in ['l', 'L']:  # line types
                            points = items[0]
                            if len(points) >= 2:
                                x0, y0 = points[0:2]
                                x1, y1 = points[-2:]
                                # Check if line is horizontal, vertical, or diagonal
                                return (abs(x0 - x1) < 5 or 
                                      abs(y0 - y1) < 5 or 
                                      abs(abs(x0 - x1) - abs(y0 - y1)) < 5)  # 45-degree lines
                return False
            
            def get_path_bounds(path):
                """Get the bounds of a path, including its stroke width"""
                bbox = fitz.Rect(path['rect'])
                # Consider stroke width in the bounds
                stroke_width = path.get('width', 1)  # Default to 1 if not specified
                bbox.x0 -= stroke_width
                bbox.y0 -= stroke_width
                bbox.x1 += stroke_width
                bbox.y1 += stroke_width
                return bbox
            
            def merge_rects(rect1, rect2, padding=10):
                """Merge two rectangles with padding"""
                x0 = min(rect1.x0, rect2.x0) - padding
                y0 = min(rect1.y0, rect2.y0) - padding
                x1 = max(rect1.x1, rect2.x1) + padding
                y1 = max(rect1.y1, rect2.y1) + padding
                return fitz.Rect(x0, y0, x1, y1)
            
            def rects_are_close(rect1, rect2, threshold=150):  # Increased threshold
                """Check if two rectangles are close to each other"""
                # Check for any kind of overlap or proximity
                expanded1 = fitz.Rect(rect1)
                expanded2 = fitz.Rect(rect2)
                # Expand rectangles by threshold
                expanded1.x0 -= threshold
                expanded1.y0 -= threshold
                expanded1.x1 += threshold
                expanded1.y1 += threshold
                expanded2.x0 -= threshold
                expanded2.y0 -= threshold
                expanded2.x1 += threshold
                expanded2.y1 += threshold
                
                # Check if the expanded rectangles intersect or are very close
                if expanded1.intersects(expanded2):
                    return True
                    
                # Check if rectangles are aligned horizontally or vertically
                horizontal_aligned = (abs(expanded1.y0 - expanded2.y0) < threshold or 
                                   abs(expanded1.y1 - expanded2.y1) < threshold)
                vertical_aligned = (abs(expanded1.x0 - expanded2.x0) < threshold or 
                                 abs(expanded1.x1 - expanded2.x1) < threshold)
                
                return horizontal_aligned or vertical_aligned
            
            # First pass: create initial clusters with special handling for axes
            clusters = []
            axis_paths = []
            
            # First identify potential axes and significant paths
            for path in paths:
                if is_likely_axis(path) or path.get('type') in ['L', 'l', 'c', 'C', 'v', 'V']:
                    axis_paths.append(get_path_bounds(path))
            
            # Create initial clusters including axes and all significant paths
            for path in paths:
                bbox = get_path_bounds(path)
                
                # More lenient size threshold
                if bbox.width < 10 or bbox.height < 10:
                    connected_to_axis = any(rects_are_close(bbox, axis, threshold=50) 
                                         for axis in axis_paths)
                    if not connected_to_axis:
                        continue
                
                # Try to add to existing cluster
                added_to_cluster = False
                for i, cluster in enumerate(clusters):
                    if rects_are_close(cluster, bbox):
                        clusters[i] = merge_rects(cluster, bbox)
                        added_to_cluster = True
                        break
                
                # Create new cluster if needed
                if not added_to_cluster:
                    clusters.append(bbox)
            
            # Second pass: aggressive merging of clusters
            merged = True
            while merged:
                merged = False
                i = 0
                while i < len(clusters):
                    j = i + 1
                    while j < len(clusters):
                        if rects_are_close(clusters[i], clusters[j]):
                            clusters[i] = merge_rects(clusters[i], clusters[j])
                            clusters.pop(j)
                            merged = True
                        else:
                            j += 1
                    i += 1
            
            # Create pixmap with higher resolution
            zoom = 2
            mat = fitz.Matrix(zoom, zoom)
            
            # Process each cluster
            for cluster_num, bbox in enumerate(clusters):
                # Add generous padding around the region
                padding = 50  # Increased padding
                bbox.x0 = max(0, bbox.x0 - padding)
                bbox.y0 = max(0, bbox.y0 - padding)
                bbox.x1 = min(rect.width, bbox.x1 + padding)
                bbox.y1 = min(rect.height, bbox.y1 + padding)
                
                # More lenient minimum size
                if bbox.width < 30 or bbox.height < 30:
                    continue
                
                # Extract the region
                pix = page.get_pixmap(matrix=mat, clip=bbox, alpha=False)
                
                # Convert to PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Convert to numpy array for analysis
                img_array = np.array(img)
                
                # More lenient uniformity check
                std_dev = np.std(img_array)
                if std_dev < 10:  # Reduced threshold
                    continue
                
                # More lenient whitespace check
                mean_value = np.mean(img_array)
                if mean_value > 252:  # Slightly more tolerant of white space
                    continue
                
                # Convert to bytes
                output = io.BytesIO()
                img.save(output, format='PNG', optimize=True)
                image_bytes = output.getvalue()
                
                # Generate unique filename
                image_hash = hashlib.md5(image_bytes).hexdigest()[:12]
                image_name = f"drawing_{page_num}_{cluster_num}_{image_hash}.png"
                
                # Store image
                self.images_by_page[page_num].append((image_name, image_bytes))
            
        except Exception as e:
            print(f"Warning: Failed to extract page region on page {page_num}: {str(e)}")
    
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
                pix = page.get_pixmap(matrix=fitz.Matrix(3, 3), alpha=False)
                
                # Convert pixmap to PNG bytes
                image_bytes = pix.tobytes("png")
                page_images.append(image_bytes)
        
        return page_images
    
    def _split_pages(self, pages: List[bytes]) -> List[List[bytes]]:
        """
        Split pages into processable chunks.
        
        Args:
            pages (List[bytes]): List of page images as bytes
            
        Returns:
            List[List[bytes]]: List of chunks, where each chunk is a list of page images
        """
        total_pages = len(pages)
        if total_pages == 0:
            return []
        
        # Calculate number of chunks
        num_chunks = min(self.max_chunks, max(1, math.ceil(total_pages / self.chunk_size)))
        
        # Calculate actual chunk size based on number of chunks
        actual_chunk_size = math.ceil(total_pages / num_chunks)
        
        # Split pages into chunks
        chunks = []
        for i in range(0, total_pages, actual_chunk_size):
            chunk = pages[i:i + actual_chunk_size]
            chunks.append(chunk)
        
        return chunks
    
    def _process_chunks_parallel(self, chunks: List[List[bytes]]) -> List[str]:
        """
        Process chunks in parallel using multiple threads.
        
        Args:
            chunks (List[List[bytes]]): List of chunks, where each chunk is a list of page images
            
        Returns:
            List[str]: List of processed content, one entry per page
        """
        all_results = []
        
        # Process a single chunk
        def process_chunk(chunk: List[bytes]) -> List[str]:
            return [self._process_page(page) for page in chunk]
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor() as executor:
            # Submit all chunks for processing
            future_to_chunk = {
                executor.submit(process_chunk, chunk): i 
                for i, chunk in enumerate(chunks)
            }
            
            # Collect results as they complete
            chunk_results = [[] for _ in chunks]
            for future in as_completed(future_to_chunk):
                chunk_idx = future_to_chunk[future]
                try:
                    result = future.result()
                    chunk_results[chunk_idx] = result
                except Exception as e:
                    print(f"Error processing chunk {chunk_idx}: {str(e)}")
                    # Insert empty strings for failed pages
                    chunk_results[chunk_idx] = ["" for _ in chunks[chunk_idx]]
        
        # Merge results from all chunks in order
        for chunk_result in chunk_results:
            all_results.extend(chunk_result)
        
        return all_results
    
    def _merge_images(self) -> List[str]:
        """Merge all images into a single array"""
        pass
    
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
