"""Thesis-service configuration shared across the researcher agents (public facade)."""

from .settings import (
    CRITIC_URL,
    LIBRARIAN_URL,
    MAX_REVISIONS,
    MCP_ARXIV_URL,
    SYNTHESIZER_URL,
)

__all__ = [
    "CRITIC_URL",
    "LIBRARIAN_URL",
    "MAX_REVISIONS",
    "MCP_ARXIV_URL",
    "SYNTHESIZER_URL",
]
