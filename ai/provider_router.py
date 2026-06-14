"""Factory / router that instantiates and caches AI providers."""

from __future__ import annotations

import importlib
from typing import Any

from .base_provider import BaseAIProvider

# ---------------------------------------------------------------------------
# Lazy-loading registry — concrete provider modules are imported on demand
# so that missing third-party packages don't break the router itself.
# ---------------------------------------------------------------------------

_PROVIDER_MODULES: dict[str, str] = {
    "ollama": ".ollama_provider",
    "openai": ".openai_provider",
    "gemini": ".gemini_provider",
}

_PROVIDER_CLASS_NAMES: dict[str, str] = {
    "ollama": "OllamaProvider",
    "openai": "OpenAIProvider",
    "gemini": "GeminiProvider",
}

_REQUIRED_CONFIG: dict[str, set[str]] = {
    "ollama": set(),
    "openai": {"api_key"},
    "gemini": {"api_key"},
}

_VALID_PROVIDERS: list[str] = sorted(_PROVIDER_MODULES.keys())


def _get_provider_class(name: str) -> type[BaseAIProvider]:
    """Import and return the provider class for *name* (lazy)."""
    try:
        mod = importlib.import_module(_PROVIDER_MODULES[name], __package__)
    except ImportError as exc:
        raise ImportError(
            f"Failed to import provider '{name}': {exc}. "
            "Make sure the required package is installed."
        ) from exc
    return getattr(mod, _PROVIDER_CLASS_NAMES[name])


class AIProviderRouter:
    """Factory and router for AI providers.

    Uses a simple instance cache so that the same provider configuration
    is reused within a process (lightweight singleton pattern).
    """

    _instances: dict[str, BaseAIProvider] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @classmethod
    def create_provider(
        cls,
        provider_name: str,
        config: dict[str, Any] | None = None,
    ) -> BaseAIProvider:
        """Create (or return a cached) provider instance.

        Args:
            provider_name: One of the supported provider keys
                (``ollama``, ``openai``, ``gemini``).
            config: Dictionary of configuration values passed to the
                provider's constructor.

        Returns:
            A ready-to-use :class:`BaseAIProvider` instance.

        Raises:
            ValueError: If the provider name is unknown.
            RuntimeError: If required config values are missing.
        """
        config = config or {}
        cache_key = cls._cache_key(provider_name, config)

        if cache_key in cls._instances:
            return cls._instances[cache_key]

        provider_name = provider_name.strip().lower()

        if provider_name not in _PROVIDER_MODULES:
            raise ValueError(
                f"Unknown provider '{provider_name}'. "
                f"Available providers: {_VALID_PROVIDERS}"
            )

        valid, msg = cls.validate_config(provider_name, config)
        if not valid:
            raise RuntimeError(f"Invalid config for '{provider_name}': {msg}")

        provider_cls = _get_provider_class(provider_name)
        instance = provider_cls(**config)
        cls._instances[cache_key] = instance
        return instance

    @classmethod
    def validate_config(
        cls,
        provider_name: str,
        config: dict[str, Any] | None = None,
    ) -> tuple[bool, str]:
        """Validate that the configuration dictionary meets requirements.

        Args:
            provider_name: One of the supported provider keys.
            config: Configuration dictionary to validate.

        Returns:
            A tuple of ``(is_valid, message)``.
        """
        provider_name = provider_name.strip().lower()
        config = config or {}

        if provider_name not in _PROVIDER_MODULES:
            return False, (
                f"Unknown provider '{provider_name}'. "
                f"Available: {_VALID_PROVIDERS}"
            )

        required = _REQUIRED_CONFIG.get(provider_name, set())
        missing = [k for k in required if k not in config]

        if missing:
            return False, f"Missing required config key(s): {', '.join(missing)}"

        return True, "Configuration is valid."

    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Return a list of registered provider names."""
        return list(_VALID_PROVIDERS)

    @classmethod
    def clear_cache(cls) -> None:
        """Remove all cached provider instances (useful in tests)."""
        cls._instances.clear()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _cache_key(provider_name: str, config: dict[str, Any]) -> str:
        """Build a deterministic cache key from provider name + config."""
        name = provider_name.strip().lower()
        items = sorted((k, str(v)) for k, v in config.items())
        serialised = ";".join(f"{k}={v}" for k, v in items)
        return f"{name}|{serialised}"
