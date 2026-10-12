from app.providers.base import ProviderError
from app.providers.groq_provider import GroqProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.ollama_provider import OllamaProvider

groq_fast = GroqProvider(model="openai/gpt-oss-20b")
gemini_strong = GeminiProvider(model="gemini-3.8-flash")
ollama_local = OllamaProvider(model="llama3.2:3b")

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
            result["skipped_providers"] = errors
            return result
        except ProviderError as e:
            errors.append(f"{provider.name}: {str(e)}")
            continue
    raise ProviderError(f"All providers failed: {'; '.join(errors)}")
