"""Typed payloads exchanged between agents over A2A (carried as JSON text)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ThesisRequest(BaseModel):
    topic: str


class Source(BaseModel):
    title: str
    summary: str
    url: str


class ResearchFindings(BaseModel):
    topic: str
    sources: list[Source] = Field(default_factory=list)
    synthesis: str


class ThesisDraft(BaseModel):
    statement: str
    argument: str
    revision: int = 0


class Critique(BaseModel):
    viable: bool
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class ThesisResult(BaseModel):
    topic: str
    statement: str
    argument: str
    viability: Critique
    sources: list[Source] = Field(default_factory=list)
    revisions: int = 0
