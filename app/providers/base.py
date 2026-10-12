from abc import ABC, abstractmethod

class ProviderError(Exception):
    pass

class BaseProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def generate(self, prompt: str, timeout: float = 10.0) -> dict:
        raise NotImplementedError
