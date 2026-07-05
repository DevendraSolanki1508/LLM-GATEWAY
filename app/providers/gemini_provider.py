"""
Gemini provider - uses Google's Gemini API (free tier).
Get a free API key at https://aistudio.google.com/apikey
"""

import os
import time
import httpx

from app.providers.base import BaseProvider, ProviderError

GEMINI_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


class GeminiProvider(BaseProvider):
    name = "gemini"

    def __init__(self, model: str = "gemini-2.5-flash"):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.model = model

    async def generate(self, prompt: str, timeout: float = 30.0) -> dict:
        if not self.api_key:
            raise ProviderError("GEMINI_API_KEY not set")

        start = time.perf_counter()

        url = GEMINI_URL_TEMPLATE.format(model=self.model)
        params = {"key": self.api_key}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "thinkingConfig": {
                    "thinkingBudget": 0
                }
            }
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, params=params, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.TimeoutException:
            raise ProviderError(f"{self.name} timed out after {timeout}s")
        except httpx.HTTPStatusError as e:
            raise ProviderError(f"{self.name} returned {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise ProviderError(f"{self.name} failed: {str(e)}")

        latency_ms = (time.perf_counter() - start) * 1000

        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            raise ProviderError(f"{self.name} returned unexpected response shape: {data}")

        return {
            "text": text,
            "provider": self.name,
            "latency_ms": round(latency_ms, 2),
        }
