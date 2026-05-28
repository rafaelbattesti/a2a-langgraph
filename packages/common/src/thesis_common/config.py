"""Environment-driven configuration. Defaults target docker-compose service names."""

from __future__ import annotations

import os


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


# --- LLM (host Ollama) ---
OLLAMA_BASE_URL = _env("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
LLAMA_MODEL = _env("LLAMA_MODEL", "llama3.1:8b")

# --- This agent's own HTTP binding / advertised URL ---
PORT = int(_env("PORT", "8080"))
PUBLIC_URL = _env("PUBLIC_URL", f"http://localhost:{PORT}")

# --- Coordinator -> specialist peers (A2A base URLs) ---
RESEARCHER_URL = _env("RESEARCHER_URL", "http://agent_researcher:8080")
CRITIC_URL = _env("CRITIC_URL", "http://agent_critic:8080")
SYNTHESIZER_URL = _env("SYNTHESIZER_URL", "http://agent_synthesizer:8080")

# --- Researcher -> arXiv MCP server (streamable-http) ---
MCP_ARXIV_URL = _env("MCP_ARXIV_URL", "http://mcp_arxiv:8000/mcp")

# --- Coordinator refine loop ---
MAX_REVISIONS = int(_env("MAX_REVISIONS", "2"))
