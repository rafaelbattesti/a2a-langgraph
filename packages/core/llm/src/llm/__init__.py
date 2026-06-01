"""Shared chat model: factory and completion helpers (public facade)."""

from .completions import complete_structured, complete_text
from .factory import build_llm

__all__ = ["build_llm", "complete_structured", "complete_text"]
