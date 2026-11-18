"""Small wrapper around the Gemini API with retries and model fallback.

Transient errors (429 / 500 / 502 / 503 / 504, network problems) are retried with
backoff, then the next model in settings.gemini_model_chain is tried, so one
overloaded model doesn't kill the whole workflow.
"""

import asyncio
import time
from typing import Optional

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.core.config import settings

# HTTP codes worth retrying or falling back on
TRANSIENT_CODES = {429, 500, 502, 503, 504}
# Go straight to the next model: 404 = retired/unknown model; 504 = the request
# already used up a full timeout, so retrying the same model just doubles the wait.
SKIP_MODEL_CODES = {404, 504}


class GeminiUnavailableError(RuntimeError):
    """No configured Gemini model could produce a response."""


class GeminiService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    async def generate_text_async(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        # The SDK call blocks, so run it in a thread to keep the event loop free
        return await asyncio.to_thread(self.generate_text, prompt, system_instruction, temperature)

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        if not self.client:
            raise GeminiUnavailableError("Gemini is not configured: GEMINI_API_KEY is not set (add it to .env).")

        if temperature is None:
            temperature = settings.GEMINI_TEMPERATURE
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_instruction,
            http_options=types.HttpOptions(timeout=settings.GEMINI_TIMEOUT_SECONDS * 1000),
        )

        failures = []
        for model in settings.gemini_model_chain:
            for attempt in range(settings.GEMINI_MAX_RETRIES + 1):
                can_retry = attempt < settings.GEMINI_MAX_RETRIES
                print(f"  [Gemini -> {model}] attempt {attempt + 1}, {len(prompt)} char prompt...", flush=True)
                try:
                    response = self.client.models.generate_content(
                        model=model, contents=prompt, config=config
                    )
                except genai_errors.APIError as e:
                    msg = f"{model}: {e.code} {e.status or ''}".strip()
                    print(f"  [Gemini x] {msg}", flush=True)
                    if e.code in SKIP_MODEL_CODES:
                        failures.append(msg)
                        break  # next model
                    if e.code in TRANSIENT_CODES:
                        if can_retry:
                            time.sleep(min(2 ** attempt, 8))
                            continue
                        failures.append(msg)
                        break  # out of retries, next model
                    raise  # 400/401/403 are config problems, another model won't help
                except Exception as e:  # network timeouts, connection resets
                    msg = f"{model}: {type(e).__name__}: {e}"[:200]
                    print(f"  [Gemini x] {msg}", flush=True)
                    is_timeout = "timeout" in type(e).__name__.lower() or "timed out" in str(e).lower()
                    if can_retry and not is_timeout:
                        time.sleep(min(2 ** attempt, 8))
                        continue
                    failures.append(msg)
                    break

                result = response.text or ""
                if not result.strip():
                    # Blocked or empty answer: treat it like a failed model
                    failures.append(f"{model}: empty response")
                    print(f"  [Gemini x] {model} returned an empty response.", flush=True)
                    break
                print(f"  [Gemini ok] {model} returned {len(result)} chars.", flush=True)
                return result

        raise GeminiUnavailableError("All Gemini models failed. " + " | ".join(failures))


gemini_service = GeminiService()
