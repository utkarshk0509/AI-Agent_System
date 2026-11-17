"""Gemini API Service Wrapper.

- generate_text_async() runs the blocking SDK call in a thread pool so it never
  blocks FastAPI's event loop.
- Transient failures (429 / 500 / 503 / 504, network timeouts) are retried with
  backoff, then the next model in settings.gemini_model_chain is tried. A single
  overloaded model therefore no longer kills the whole workflow.
- A missing API key raises GeminiUnavailableError instead of returning stub text
  (stub text used to be fed to the sandbox as "code" and fail every iteration).
"""

import os
import time
import asyncio
from typing import Optional
from app.core.config import settings

try:
    from google import genai
    from google.genai import types
    from google.genai import errors as genai_errors
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# HTTP codes worth retrying / falling back on
_TRANSIENT_CODES = {429, 500, 502, 503, 504}
# Skip straight to the next model: 404 = retired/unknown model; 504 = the
# request already burned a full timeout, retrying the same model just doubles it.
_MODEL_UNUSABLE_CODES = {404, 504}


class GeminiUnavailableError(RuntimeError):
    """Raised when no configured Gemini model could produce a response."""


class GeminiService:
    """Async-safe wrapper for the Gemini model family with retry + model fallback."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name  # None = use settings.gemini_model_chain

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
        return await asyncio.to_thread(
            self.generate_text, prompt, system_instruction, temperature
        )

    def _model_chain(self) -> list[str]:
        if self.model_name:
            return [self.model_name]
        return settings.gemini_model_chain

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        if not self.client:
            reason = (
                "google-genai package is not installed"
                if not GENAI_AVAILABLE
                else "GEMINI_API_KEY is not set (add it to .env)"
            )
            raise GeminiUnavailableError(f"Gemini is not configured: {reason}.")

        config = types.GenerateContentConfig(
            temperature=temperature if temperature is not None else settings.GEMINI_TEMPERATURE,
            system_instruction=system_instruction,
            http_options=types.HttpOptions(timeout=settings.GEMINI_TIMEOUT_SECONDS * 1000),
        )

        failures: list[str] = []
        for model in self._model_chain():
            for attempt in range(settings.GEMINI_MAX_RETRIES + 1):
                print(f"  [Gemini -> {model}] attempt {attempt + 1}, {len(prompt)} char prompt...", flush=True)
                try:
                    response = self.client.models.generate_content(
                        model=model, contents=prompt, config=config
                    )
                except genai_errors.APIError as e:
                    code = getattr(e, "code", None)
                    msg = f"{model}: {code} {getattr(e, 'status', '')}".strip()
                    print(f"  [Gemini x] {msg}", flush=True)
                    if code in _MODEL_UNUSABLE_CODES:
                        failures.append(msg)
                        break  # next model
                    if code in _TRANSIENT_CODES:
                        if attempt < settings.GEMINI_MAX_RETRIES:
                            time.sleep(min(2 ** attempt, 8))
                            continue
                        failures.append(msg)
                        break  # retries exhausted -> next model
                    raise  # 400/401/403: config problem, falling back won't help
                except Exception as e:  # network timeouts, connection resets
                    msg = f"{model}: {type(e).__name__}: {e}"
                    print(f"  [Gemini x] {msg[:200]}", flush=True)
                    is_timeout = "timeout" in type(e).__name__.lower() or "timed out" in str(e).lower()
                    if attempt < settings.GEMINI_MAX_RETRIES and not is_timeout:
                        time.sleep(min(2 ** attempt, 8))
                        continue
                    failures.append(msg[:200])
                    break

                result = response.text or ""
                if not result.strip():
                    # Blocked / empty candidate: treat like a model failure
                    failures.append(f"{model}: empty response")
                    print(f"  [Gemini x] {model} returned an empty response.", flush=True)
                    break
                print(f"  [Gemini ok] {model} returned {len(result)} chars.", flush=True)
                return result

        raise GeminiUnavailableError(
            "All Gemini models failed. " + " | ".join(failures)
        )


# Singleton instance shared across all graph nodes
gemini_service = GeminiService()
