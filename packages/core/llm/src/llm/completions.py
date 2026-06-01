"""Completion helpers over the shared chat model."""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from .factory import build_llm

T = TypeVar("T", bound=BaseModel)


async def complete_text(system: str, human: str, temperature: float = 0.3) -> str:
    llm = build_llm(temperature=temperature)
    response = await llm.ainvoke([("system", system), ("human", human)])
    return response.content


async def complete_structured(
    schema: type[T], system: str, human: str, temperature: float = 0.1
) -> T:
    llm = build_llm(temperature=temperature).with_structured_output(schema)
    return await llm.ainvoke([("system", system), ("human", human)])
