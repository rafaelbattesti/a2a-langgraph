"""Factory and helpers for the shared chat model backed by host Ollama."""

from __future__ import annotations

from typing import TypeVar

from langchain_ollama import ChatOllama
from pydantic import BaseModel

from . import config

T = TypeVar("T", bound=BaseModel)


def build_llm(temperature: float = 0.2, **kwargs) -> ChatOllama:
    return ChatOllama(
        model=config.LLAMA_MODEL,
        base_url=config.OLLAMA_BASE_URL,
        temperature=temperature,
        **kwargs,
    )


async def complete_text(system: str, human: str, temperature: float = 0.3) -> str:
    llm = build_llm(temperature=temperature)
    response = await llm.ainvoke([("system", system), ("human", human)])
    return response.content


async def complete_structured(
    schema: type[T], system: str, human: str, temperature: float = 0.1
) -> T:
    llm = build_llm(temperature=temperature).with_structured_output(schema)
    return await llm.ainvoke([("system", system), ("human", human)])
