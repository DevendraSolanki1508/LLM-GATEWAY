"""
Router: given a complexity level, returns an ordered list of providers
to try. First one that succeeds wins. If all fail, we raise.
"""

from app.providers.base import ProviderError
from app.providers.groq_provider import GroqProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.ollama_provider import OllamaProvider

# Instantiate providers once (reused across requests)
groq_fast = GroqProvider(model="llama-3.1-8b-instant")
gemini_strong = GeminiProvider(model="gemini-2.5-flash")
ollama_local = OllamaProvider(model="llama3.2:3b")

# Routing table: complexity -> ordered provider preference.
# Simple queries go to the fastest/cheapest option first.
# Complex queries go to the stronger reasoning model first.
# Ollama (local, free) is the last-resort fallback for both.
ROUTES = {
    "simple": [groq_fast, gemini_strong, ollama_local],
    "complex": [gemini_strong, groq_fast, ollama_local],
}


async def route_request(prompt: str, complexity: str) -> dict:
    providers = ROUTES.get(complexity, ROUTES["simple"])
    errors = []

    for provider in providers:
        try:
            result = await provider.generate(prompt)
            result["complexity"] = complexity
            result["fallback_used"] = provider != providers[0]
            result["skipped_providers"] = errors  # shows why earlier providers were skipped
            return result
        except ProviderError as e:
            errors.append(f"{provider.name}: {str(e)}")
            continue  # try next provider

    raise ProviderError(f"All providers failed: {'; '.join(errors)}")

