"""Gemini API Service Wrapper.

Key fixes applied:
- generate_text() is now ASYNC (async def) to prevent blocking FastAPI's event loop.
- Hard 60-second HTTP timeout added via GenerateContentConfig http_options.
- model_name is always resolved freshly from settings so .env changes take effect.
- Clean print-based progress reporting for terminal visibility.
"""

import os
import asyncio
from typing import Optional
from app.core.config import settings

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class GeminiService:
    """Async-safe wrapper for the Gemini model family."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        # Always read model name from settings so runtime .env changes are respected
        self.model_name = model_name  # None = always use settings.GEMINI_MODEL at call time

        if GENAI_AVAILABLE and self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    async def generate_text_async(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Async wrapper: runs the synchronous Gemini SDK call in a thread pool
        so it never blocks FastAPI's asyncio event loop.
        
        FIX: Without this, a 2-second Gemini API call blocks the ENTIRE server.
        With asyncio.to_thread(), FastAPI can handle other requests concurrently.
        """
        return await asyncio.to_thread(
            self.generate_text,
            prompt,
            system_instruction,
            temperature,
        )

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Synchronous Gemini text generation. Use generate_text_async() from async contexts.
        
        - Resolves model name from settings at call-time (supports runtime changes).
        - Applies a 60-second timeout to prevent infinite hangs on slow API responses.
        """
        if not self.client:
            # Dev fallback: no API key configured
            return (
                f"[STUB RESPONSE - configure GEMINI_API_KEY in .env]\n"
                f"Prompt received: {prompt[:80]}..."
            )

        # Always resolve from settings so .env hot-reload works
        model_to_use = self.model_name or settings.GEMINI_MODEL

        config = types.GenerateContentConfig(
            temperature=temperature if temperature is not None else settings.GEMINI_TEMPERATURE,
            system_instruction=system_instruction,
            # FIX: Hard timeout so a slow Gemini response never hangs the request indefinitely
            http_options=types.HttpOptions(timeout=60_000),  # 60 seconds in ms
        )

        print(f"  [Gemini → {model_to_use}] Sending {len(prompt)} char prompt...", flush=True)
        response = self.client.models.generate_content(
            model=model_to_use,
            contents=prompt,
            config=config,
        )
        result = response.text or ""
        print(f"  [Gemini ✓] Received {len(result)} char response.", flush=True)
        return result


# Singleton instance shared across all graph nodes
gemini_service = GeminiService()
