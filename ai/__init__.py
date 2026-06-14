from .base_provider import BaseAIProvider
from .provider_router import AIProviderRouter

__all__ = [
    "BaseAIProvider",
    "AIProviderRouter",
    "OllamaProvider",
    "OpenAIProvider",
    "GeminiProvider",
]

# -------------------------------------------------------------------
# Lazy provider imports — each concrete provider may require
# third-party packages that aren't installed in every environment.
# -------------------------------------------------------------------


def __getattr__(name: str):
    import importlib

    if name == "OllamaProvider":
        import importlib

        mod = importlib.import_module(".ollama_provider", __package__)
        return mod.OllamaProvider
    if name == "OpenAIProvider":
        mod = importlib.import_module(".openai_provider", __package__)
        return mod.OpenAIProvider
    if name == "GeminiProvider":
        mod = importlib.import_module(".gemini_provider", __package__)
        return mod.GeminiProvider
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
