"""Gemini provider — uses the google-genai Python SDK."""

from __future__ import annotations

from typing import Generator

from google import genai
from google.genai import types as genai_types

from .base_provider import BaseAIProvider


class GeminiProvider(BaseAIProvider):
    """AI provider backed by Google's Gemini models."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-pro",
    ) -> None:
        """Initialise the provider with credentials and model selection.

        Args:
            api_key: Google AI Studio API key.
            model: Gemini model name (default gemini-pro).
        """
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
    ) -> str:
        """Generate a complete (non-streamed) response from Gemini."""
        config = self._build_config(temperature)
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=[system_prompt, prompt] if system_prompt else prompt,
                config=config,
            )
            return response.text or ""
        except Exception as exc:
            raise RuntimeError(f"Gemini API error: {exc}") from exc

    def generate_stream(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """Stream a response from Gemini, yielding text chunks."""
        config = self._build_config(temperature)
        try:
            stream = self._client.models.generate_content_stream(
                model=self._model,
                contents=[system_prompt, prompt] if system_prompt else prompt,
                config=config,
            )
            for chunk in stream:
                if chunk.text:
                    yield chunk.text
        except Exception as exc:
            raise RuntimeError(
                f"Gemini streaming error: {exc}"
            ) from exc

    def get_embedding(self, text: str) -> list[float]:
        """Compute an embedding vector using the Gemini embedding model."""
        try:
            result = self._client.models.embed_content(
                model="models/text-embedding-004",
                contents=text,
            )
            return result.embeddings[0].values or []
        except Exception as exc:
            raise RuntimeError(
                f"Gemini embedding error: {exc}"
            ) from exc

    @property
    def name(self) -> str:
        """Human-readable provider identifier."""
        return "Gemini"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_config(temperature: float) -> genai_types.GenerateContentConfig:
        return genai_types.GenerateContentConfig(
            temperature=temperature,
        )
