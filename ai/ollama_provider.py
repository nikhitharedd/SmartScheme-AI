"""Ollama provider — connects to a local Ollama instance."""

from __future__ import annotations

import json
from typing import Any, Generator

import requests

from .base_provider import BaseAIProvider


class OllamaProvider(BaseAIProvider):
    """AI provider that communicates with a locally-hosted Ollama server."""

    def __init__(
        self,
        endpoint: str = "http://localhost:11434",
        model: str = "llama3",
    ) -> None:
        """Initialise the provider with server connection details.

        Args:
            endpoint: Base URL of the Ollama server.
            model: Name of the model to use (e.g. llama3, mistral).
        """
        self._endpoint = endpoint.rstrip("/")
        self._model = model
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_payload(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float,
        stream: bool,
    ) -> dict[str, Any]:
        return {
            "model": self._model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": stream,
            "options": {"temperature": temperature},
        }

    def _raise_for_status(self, response: requests.Response) -> None:
        """Check the response and raise a descriptive exception on failure."""
        try:
            response.raise_for_status()
        except requests.RequestException as exc:
            detail = response.text[:500] if response.text else str(exc)
            raise RuntimeError(
                f"Ollama API error ({response.status_code}): {detail}"
            ) from exc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
    ) -> str:
        """Generate a complete (non-streamed) response from Ollama."""
        payload = self._build_payload(prompt, system_prompt, temperature, stream=False)
        try:
            resp = self._session.post(
                f"{self._endpoint}/api/generate",
                data=json.dumps(payload),
                timeout=120,
            )
            self._raise_for_status(resp)
            data = resp.json()
            return data.get("response", "")
        except requests.RequestException as exc:
            raise RuntimeError(f"Failed to reach Ollama server: {exc}") from exc

    def generate_stream(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """Stream tokens from Ollama, yielding each chunk as it arrives."""
        payload = self._build_payload(prompt, system_prompt, temperature, stream=True)
        try:
            with self._session.post(
                f"{self._endpoint}/api/generate",
                data=json.dumps(payload),
                stream=True,
                timeout=300,
            ) as resp:
                self._raise_for_status(resp)
                for line in resp.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    chunk = json.loads(line)
                    token = chunk.get("response", "")
                    if token:
                        yield token
                    if chunk.get("done", False):
                        break
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Streaming error from Ollama server: {exc}"
            ) from exc

    def get_embedding(self, text: str) -> list[float]:
        """Compute an embedding vector via the Ollama embeddings API."""
        payload = {"model": self._model, "prompt": text}
        try:
            resp = self._session.post(
                f"{self._endpoint}/api/embeddings",
                data=json.dumps(payload),
                timeout=60,
            )
            self._raise_for_status(resp)
            data = resp.json()
            return data.get("embedding", [])
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Failed to get embedding from Ollama: {exc}"
            ) from exc

    @property
    def name(self) -> str:
        """Human-readable provider identifier."""
        return "Ollama"
