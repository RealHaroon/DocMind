from abc import ABC, abstractmethod
from collections.abc import Iterator


class ProviderError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, system: str, prompt: str, model: str) -> str:
        """Generate an answer using one explicitly configured provider."""

    @abstractmethod
    def stream(self, system: str, prompt: str, model: str) -> Iterator[str]:
        """Yield generated text in order."""
