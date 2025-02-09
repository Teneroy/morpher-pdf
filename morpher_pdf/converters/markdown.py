from typing import List
from . import BaseConverter, Page, PDFImage, PageImage
from llm.prompts import MARKDOWN_CONVERTER_PROMPT, MARKDOWN_JUDGE_PROMPT, MARKDOWN_CONVERTER_PROMPT_GEMINI_2, MARKDOWN_CONVERTER_PROMPT_GEMINI_2_v1

class MarkdownConverter(BaseConverter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def _process_page(self, page: Page) -> str:
        """Convert page to Markdown using LLM"""
        # Find the corresponding page object
        # page = next((p for p in self.pages if p.page_number == page_number), None)
        # if not page:
        #     return ""
            
        # Process the page content with LLM
        markdown = self._rewrite_page(
            self.llm_client.process_image(
                page.page_image.image_bytes, 
                MARKDOWN_CONVERTER_PROMPT_GEMINI_2_v1.format(
                    images=[img.name for img in page.images]
                )
            )
        )
        
        return markdown if markdown else ""
    
    def _merge_content(self) -> str:
        """Merge content with Markdown-specific formatting"""
        # Sort pages by page number to ensure correct order
        sorted_pages = sorted(self.pages, key=lambda p: p.page_number)
        
        # Join pages with proper markdown formatting
        merged_content = "\n\n".join(
            page.content for page in sorted_pages if page.content
        )
        
        return merged_content
