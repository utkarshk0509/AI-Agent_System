"""Gemini 2.5 API Service Wrapper.

Provides an abstraction layer for Gemini 2.5 Pro/Flash calls, supporting
system instructions, temperature controls, and response extraction.
"""

import os
from typing import Optional
from app.core.config import settings

# Attempt import of Google GenAI SDK (google-genai / google.genai)
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class GeminiService:
    """Wrapper for interacting with the Gemini 2.5 model family."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name or settings.GEMINI_MODEL
        
        if GENAI_AVAILABLE and self.api_key:
            # Initialize official Google GenAI client
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Synchronously generate text using Gemini 2.5.
        
        Args:
            prompt: User or contextual prompt text.
            system_instruction: System prompt to steer agent behavior.
            temperature: Sampling temperature (e.g., 0.1 for deterministic code).
            
        Returns:
            The raw text response from Gemini.
        """
        if not self.client:
            # Fallback/stub for local development before an API key is wired up
            return (
                f"[STUB GEMINI RESPONSE for '{prompt[:40]}...']\n"
                "Please configure GEMINI_API_KEY in .env to invoke live Gemini 2.5 API."
            )

        config = types.GenerateContentConfig(
            temperature=temperature if temperature is not None else settings.GEMINI_TEMPERATURE,
            system_instruction=system_instruction,
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config,
        )
        return response.text or ""


# Singleton instance for dependency injection across graph nodes
gemini_service = GeminiService()

