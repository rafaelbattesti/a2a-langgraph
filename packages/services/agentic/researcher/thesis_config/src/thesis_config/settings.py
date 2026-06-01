"""Thesis-service configuration: specialist peer URLs, arXiv MCP, refine loop.

Platform-level settings live in the shared ``config`` package; this module holds
only thesis-capability settings.
"""

from __future__ import annotations

import os


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


# --- Coordinator -> specialist peers (A2A base URLs) ---
LIBRARIAN_URL = _env("LIBRARIAN_URL", "http://agent_librarian:8080")
CRITIC_URL = _env("CRITIC_URL", "http://agent_critic:8080")
SYNTHESIZER_URL = _env("SYNTHESIZER_URL", "http://agent_synthesizer:8080")

# --- Librarian -> arXiv MCP server (streamable-http) ---
MCP_ARXIV_URL = _env("MCP_ARXIV_URL", "http://mcp_arxiv:8000/mcp")

# --- Coordinator refine loop ---
MAX_REVISIONS = int(_env("MAX_REVISIONS", "2"))
