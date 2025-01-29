import base64
from openai import OpenAI
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
                            "text": "Translate the following image in German. Return the text in MD format preserving the original formatting. Every formula should be in LaTeX format.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                }
            ],
        )
        print(response.choices[0].message.content)
        return response.choices[0].message.content
    
    def _merge_content(self) -> str:
        """Merge content with Markdown-specific formatting"""
        # Join pages with proper markdown formatting
        # Handle image references in markdown format
        merged_content = "\n\n".join(self.page_contents)
        return merged_content
