import time

from app.providers.base import ProviderError
from app.providers.groq_provider import GroqProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.ollama_provider import OllamaProvider

groq_fast = GroqProvider(model="openai/gpt-oss-20b")
gemini_strong = GeminiProvider(model="gemini-3.1-flash-lite")
ollama_local = OllamaProvider(model="llama3.2:3b")

ROUTES = {
    "simple": [groq_fast, gemini_strong, ollama_local],
    "complex": [gemini_strong, groq_fast, ollama_local],
}

FAILURE_THRESHOLD = 3     # consecutive failures before a provider is skipped
COOLDOWN_SECONDS = 60     # how long a tripped provider is skipped


class CircuitBreaker:
    """
    Skips a provider after repeated failures so requests don't wait on a
    provider that is known to be down. After the cooldown, the next request
    is allowed through as a trial: success closes the breaker, and a single
    failure re-opens it.
    """

    def __init__(self, threshold: int = FAILURE_THRESHOLD, cooldown: float = COOLDOWN_SECONDS):
        self.threshold = threshold
        self.cooldown = cooldown
        self.failures: dict[str, int] = {}
        self.open_until: dict[str, float] = {}

    def is_open(self, name: str) -> bool:
        return time.monotonic() < self.open_until.get(name, 0.0)

    def record_success(self, name: str) -> None:
        self.failures[name] = 0
        self.open_until[name] = 0.0

    def record_failure(self, name: str) -> None:
        self.failures[name] = self.failures.get(name, 0) + 1
        if self.failures[name] >= self.threshold:
            self.open_until[name] = time.monotonic() + self.cooldown


breaker = CircuitBreaker()


async def route_request(prompt: str, complexity: str) -> dict:
    providers = ROUTES.get(complexity, ROUTES["simple"])
    errors = []

    candidates = []
    for provider in providers:
        if breaker.is_open(provider.name):
            errors.append(f"{provider.name}: circuit open, skipped")
        else:
            candidates.append(provider)

    # If every provider is tripped, try them all rather than fail instantly
    if not candidates:
        candidates = providers

    for provider in candidates:
        try:
            result = await provider.generate(prompt)
            breaker.record_success(provider.name)
            result["complexity"] = complexity
            result["fallback_used"] = provider != providers[0]
            result["skipped_providers"] = errors
            return result
        except ProviderError as e:
            breaker.record_failure(provider.name)
            errors.append(f"{provider.name}: {str(e)}")
            continue

    raise ProviderError(f"All providers failed: {'; '.join(errors)}")