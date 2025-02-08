from abc import ABC, abstractmethod
import base64
import json
from typing import Any, Dict
from openai import OpenAI
import google.generativeai as genai
from llm.prompts import MARKDOWN_CONVERTER_PROMPT
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from langfuse.decorators import observe


class BaseLLMClient(ABC):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._setup_client()
    
    @abstractmethod
    def _setup_client(self) -> None:
        """Initialize the specific client"""
        pass

    @abstractmethod
    def process_image(self, image_bytes: bytes, prompt: str) -> str:
        """Process image with the LLM and return the response"""
        pass

    @abstractmethod
    def correct_result(self, result: str, prompt: str) -> str:
        """Correct the result of the LLM"""
        pass

class GPT4VisionClient(BaseLLMClient):
    def _setup_client(self) -> None:
        self.client = OpenAI(api_key=self.api_key)
    
    @observe()
    def process_image(self, image_bytes: bytes, prompt: str = MARKDOWN_CONVERTER_PROMPT) -> str:
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                        },
                    ],
                }
            ],
            temperature=0,
            frequency_penalty=0,
            presence_penalty=0,
            top_p=1,
        )

        return response.choices[0].message.content
    
    def correct_result(self, result: str, image_bytes: bytes, prompt: str) -> str:
        pass

class GeminiFlash1Client(BaseLLMClient):
    def _setup_client(self) -> None:
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def process_image(self, image_bytes: bytes, prompt: str=MARKDOWN_CONVERTER_PROMPT) -> str:
        response = self.model.generate_content(
            contents=[prompt, {"mime_type": "image/png", "data": image_bytes}],
            generation_config={"temperature": 0.3}
        )
        return response.text
    
    def correct_result(self, result: str, image_bytes: bytes, prompt: str) -> str:
        pass

class GeminiFlash2Client(BaseLLMClient):
    def _setup_client(self) -> None:
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-001')
    
    @observe()
    def process_image(self, image_bytes: bytes, prompt: str=MARKDOWN_CONVERTER_PROMPT) -> str:
        # safety_settings_b64 = "e30="  # @param {isTemplate: true}
        # safety_settings = json.loads(base64.b64decode(safety_settings_b64))
        response = self.model.generate_content(
            contents=[prompt, {"mime_type": "image/png", "data": image_bytes}],
            safety_settings = [{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}],
            generation_config={"temperature": 0.1}
        )
        return response.text
    
    @observe()
    def correct_result(self, result: str, image_bytes: bytes, prompt: str) -> str:
        response = self.model.generate_content(
            contents=[prompt, {"mime_type": "image/png", "data": image_bytes}, result],
            generation_config={"temperature": 0}
        )
        print(response.text)
        return response.text

class GrokAIClient(BaseLLMClient):
    def _setup_client(self) -> None:
        self.client = OpenAI(api_key=self.api_key, base_url="https://api.x.ai/v1")
    
    def process_image(self, image_bytes: bytes, prompt: str = MARKDOWN_CONVERTER_PROMPT) -> str:
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        response = self.client.chat.completions.create(
            model="grok-2-vision-latest",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                        },
                    ],
                }
            ],
            temperature=0,
        )

        return response.choices[0].message.content
    
    def correct_result(self, result: str, image_bytes: bytes, prompt: str) -> str:
        pass