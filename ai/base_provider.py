"""Abstract base class for all AI providers in SmartScheme AI."""

from abc import ABCMeta, abstractmethod
from typing import Generator


class BaseAIProvider(metaclass=ABCMeta):
    """Abstract base class that defines the interface for all AI providers.

    All concrete providers (Ollama, OpenAI, Gemini) must implement
    these methods to ensure consistent behaviour across the system.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
    ) -> str:
        """Send a prompt to the model and return the complete response text.

        Args:
            prompt: The user message / input prompt.
            system_prompt: An optional system-level instruction.
            temperature: Sampling temperature (0.0 – 2.0).

        Returns:
            The model's response as a single string.
        """

    @abstractmethod
    def generate_stream(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """Send a prompt and stream the response tokens one by one.

        Args:
            prompt: The user message / input prompt.
            system_prompt: An optional system-level instruction.
            temperature: Sampling temperature (0.0 – 2.0).

        Yields:
            Individual text chunks / tokens as they are produced.
        """

    @abstractmethod
    def get_embedding(self, text: str) -> list[float]:
        """Compute a vector embedding for the given text.

        Args:
            text: The text to embed.

        Returns:
            A list of floats representing the embedding vector.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return a human-readable identifier for this provider."""
