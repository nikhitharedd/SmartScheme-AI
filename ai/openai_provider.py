"""OpenAI provider — uses the official openai Python SDK."""

from __future__ import annotations

from typing import Generator

from openai import APIError, OpenAI

from .base_provider import BaseAIProvider


class OpenAIProvider(BaseAIProvider):
    """AI provider backed by OpenAI's API (GPT, embeddings, etc.)."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
    ) -> None:
        """Initialise the provider with credentials and model selection.

        Args:
            api_key: OpenAI API key.
            model: Chat model name (default gpt-4o-mini).
        """
        self._client = OpenAI(api_key=api_key)
        self._model = model
        self._embedding_model = "text-embedding-3-small"

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
    ) -> str:
        """Generate a complete chat completion response.

        Builds a conversation with an optional system message followed
        by the user prompt.
        """
        messages = self._build_messages(prompt, system_prompt)
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                stream=False,
            )
            return response.choices[0].message.content or ""
        except APIError as exc:
            raise RuntimeError(f"OpenAI API error: {exc}") from exc

    def generate_stream(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """Stream a chat completion, yielding content delta chunks."""
        messages = self._build_messages(prompt, system_prompt)
        try:
            stream = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content
        except APIError as exc:
            raise RuntimeError(
                f"OpenAI streaming error: {exc}"
            ) from exc

    def get_embedding(self, text: str) -> list[float]:
        """Compute a text embedding using the configured embedding model."""
        try:
            response = self._client.embeddings.create(
                model=self._embedding_model,
                input=text,
            )
            return response.data[0].embedding
        except APIError as exc:
            raise RuntimeError(
                f"OpenAI embedding error: {exc}"
            ) from exc

    @property
    def name(self) -> str:
        """Human-readable provider identifier."""
        return "OpenAI"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_messages(
        prompt: str,
        system_prompt: str,
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages
