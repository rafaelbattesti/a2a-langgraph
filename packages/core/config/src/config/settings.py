"""Environment-driven platform settings.

Capability-agnostic: holds only platform-level settings (process binding, the
shared model endpoint, log level). Service-specific settings live with the
service that owns them.
"""

from __future__ import annotations

import os


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


# --- Shared chat model (host Ollama) ---
OLLAMA_BASE_URL = _env("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
LLAMA_MODEL = _env("LLAMA_MODEL", "llama3.1:8b")

# --- This service's own HTTP binding / advertised URL ---
PORT = int(_env("PORT", "8080"))
PUBLIC_URL = _env("PUBLIC_URL", f"http://localhost:{PORT}")
LOG_LEVEL = _env("LOG_LEVEL", "INFO")
