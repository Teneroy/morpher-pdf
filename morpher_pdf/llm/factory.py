from enum import Enum
from typing import Optional
from .clients import BaseLLMClient, GPT4VisionClient, GeminiFlash1Client, GeminiFlash2Client, GrokAIClient

class LLMType(Enum):
    GPT4_VISION = "gpt4-vision"
    GEMINI_FLASH_1 = "gemini-flash-1"
    GEMINI_FLASH_2 = "gemini-flash-2"
    GROK_AI = "grok-ai"

class LLMFactory:
    @staticmethod
    def create_client(llm_type: LLMType, api_key: str) -> BaseLLMClient:
        """
        Create an LLM client based on the specified type.
        
        Args:
            llm_type (LLMType): Type of LLM client to create
            api_key (str): API key for the service
            
        Returns:
            BaseLLMClient: Configured LLM client
            
        Raises:
            ValueError: If llm_type is not supported
        """
        if isinstance(llm_type, str):
            try:
                llm_type = LLMType(llm_type)
            except ValueError:
                raise ValueError(f"Unsupported LLM type: {llm_type}")

        clients = {
            LLMType.GPT4_VISION: GPT4VisionClient,
            LLMType.GEMINI_FLASH_1: GeminiFlash1Client,
            LLMType.GEMINI_FLASH_2: GeminiFlash2Client,
            LLMType.GROK_AI: GrokAIClient
        }
        
        client_class = clients.get(llm_type)
        if not client_class:
            raise ValueError(f"Unsupported LLM type: {llm_type}")
        
        return client_class(api_key=api_key) 