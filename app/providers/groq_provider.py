"""
Groq provider - uses Groq's free, extremely fast inference API.
Get a free API key at https://console.groq.com/keys
"""

import os
import time
import httpx

from app.providers.base import BaseProvider, ProviderError

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqProvider(BaseProvider):
    name = "groq"

    def __init__(self, model: str = "llama-3.1-8b-instant"):
        self.api_key = os.environ.get("GROQ_API_KEY")
        self.model = model

    async def generate(self, prompt: str, timeout: float = 10.0) -> dict:
        if not self.api_key:
            raise ProviderError("GROQ_API_KEY not set")

        start = time.perf_counter()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(GROQ_URL, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.TimeoutException:
            raise ProviderError(f"{self.name} timed out after {timeout}s")
        except httpx.HTTPStatusError as e:
            raise ProviderError(f"{self.name} returned {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise ProviderError(f"{self.name} failed: {str(e)}")

        latency_ms = (time.perf_counter() - start) * 1000
        text = data["choices"][0]["message"]["content"]

        return {
            "text": text,
            "provider": self.name,
            "latency_ms": round(latency_ms, 2),
        }
