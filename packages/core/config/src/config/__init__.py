"""Environment-driven platform settings shared across services (public facade)."""

from .settings import LLAMA_MODEL, LOG_LEVEL, OLLAMA_BASE_URL, PORT, PUBLIC_URL

__all__ = ["LLAMA_MODEL", "LOG_LEVEL", "OLLAMA_BASE_URL", "PORT", "PUBLIC_URL"]
