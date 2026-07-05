"""
Ollama provider - calls a locally running Ollama instance.
Requires Ollama installed and running: https://ollama.com
Pull a model first, e.g.: `ollama pull llama3.2:3b`
"""

import time
import httpx

from app.providers.base import BaseProvider, ProviderError

OLLAMA_URL = "http://localhost:11434/api/generate"


class OllamaProvider(BaseProvider):
    name = "ollama"

    def __init__(self, model: str = "llama3.2:3b"):
        self.model = model

    async def generate(self, prompt: str, timeout: float = 30.0) -> dict:
        start = time.perf_counter()

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(OLLAMA_URL, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.ConnectError:
            raise ProviderError(f"{self.name} not reachable - is Ollama running?")
        except httpx.TimeoutException:
            raise ProviderError(f"{self.name} timed out after {timeout}s")
        except Exception as e:
            raise ProviderError(f"{self.name} failed: {str(e)}")

        latency_ms = (time.perf_counter() - start) * 1000

        return {
            "text": data.get("response", ""),
            "provider": self.name,
            "latency_ms": round(latency_ms, 2),
        }
