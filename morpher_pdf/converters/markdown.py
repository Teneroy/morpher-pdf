from . import BaseConverter

class MarkdownConverter(BaseConverter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def _process_page(self, page: bytes) -> str:
        """Convert chunk to Markdown using LLM"""
        return self._rewrite_page(self.llm_client.process_image(page))
    
    def _merge_content(self) -> str:
        """Merge content with Markdown-specific formatting"""
        # Join pages with proper markdown formatting
        # Handle image references in markdown format
        merged_content = "\n\n".join(self.page_contents)
        return merged_content
