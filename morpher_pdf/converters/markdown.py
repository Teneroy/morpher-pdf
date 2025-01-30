import base64
from openai import OpenAI

from llm.prompts import MARKDOWN_CONVERTER_PROMPT
from . import BaseConverter
from typing import List

class MarkdownConverter(BaseConverter):
    def _process_page(self, page: bytes) -> str:
        """Convert chunk to Markdown using LLM"""
        client = OpenAI(api_key=self.openai_key)
        # Getting the Base64 string
        base64_image = base64.b64encode(page).decode("utf-8")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": MARKDOWN_CONVERTER_PROMPT,
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                        },
                    ],
                }
            ],
            temperature=0.3,
        )
        # self._rewrite_page(response.choices[0].message.content)
        return self._rewrite_page(response.choices[0].message.content)
    
    def _merge_content(self) -> str:
        """Merge content with Markdown-specific formatting"""
        # Join pages with proper markdown formatting
        # Handle image references in markdown format
        merged_content = "\n\n".join(self.page_contents)
        return merged_content
