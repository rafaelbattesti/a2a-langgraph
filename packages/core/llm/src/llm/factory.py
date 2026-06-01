"""Factory for the shared chat model backed by host Ollama."""

from __future__ import annotations

import config
from langchain_ollama import ChatOllama


def build_llm(temperature: float = 0.2, **kwargs) -> ChatOllama:
    return ChatOllama(
        model=config.LLAMA_MODEL,
        base_url=config.OLLAMA_BASE_URL,
        temperature=temperature,
        **kwargs,
    )
