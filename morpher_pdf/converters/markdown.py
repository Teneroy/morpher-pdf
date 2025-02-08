from . import BaseConverter
from llm.prompts import MARKDOWN_CONVERTER_PROMPT, MARKDOWN_JUDGE_PROMPT, MARKDOWN_CONVERTER_PROMPT_GEMINI_2, MARKDOWN_CONVERTER_PROMPT_GEMINI_2_v1

class MarkdownConverter(BaseConverter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def _process_page(self, page: bytes, page_number: int) -> str:
        """Convert chunk to Markdown using LLM"""
        markdown = self._rewrite_page(self.llm_client.process_image(page, MARKDOWN_CONVERTER_PROMPT_GEMINI_2_v1.format(images=[image[0] for image in self.images_by_page[page_number]])))
        # return self._rewrite_page(self.llm_judge.correct_result(markdown, page, MARKDOWN_JUDGE_PROMPT.format(images=[image[0] for image in self.images_by_page[page_number]])))
        return markdown
    
    def _merge_content(self) -> str:
        """Merge content with Markdown-specific formatting"""
        # Join pages with proper markdown formatting
        # Handle image references in markdown format
        merged_content = "\n".join(self.page_contents)
        return merged_content
