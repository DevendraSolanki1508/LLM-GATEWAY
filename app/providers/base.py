"""
Base interface every LLM provider must implement.
This is what makes the gateway "pluggable" - add a new provider
by just implementing this class, no changes needed elsewhere.
"""

from abc import ABC, abstractmethod


class ProviderError(Exception):
    """Raised when a provider fails to respond (timeout, rate limit, etc.)"""
    pass


class BaseProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def generate(self, prompt: str, timeout: float = 10.0) -> dict:
        """
        Send prompt to the LLM and return a standardized response.

        Returns:
            {
                "text": str,          # the model's answer
                "provider": str,      # which provider handled it
                "latency_ms": float,  # how long it took
            }

        Raises:
            ProviderError if the call fails for any reason.
        """
        raise NotImplementedError
