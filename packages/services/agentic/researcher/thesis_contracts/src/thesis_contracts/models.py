"""Thesis-capability payload models exchanged over A2A structured data parts."""

from __future__ import annotations

from contracts import ContractModel
from pydantic import Field


class ThesisRequest(ContractModel):
    topic: str = Field(min_length=1)


class Source(ContractModel):
    title: str
    summary: str
    url: str


class ResearchFindings(ContractModel):
    topic: str = Field(min_length=1)
    sources: list[Source] = Field(default_factory=list)
    synthesis: str


class ThesisDraft(ContractModel):
    statement: str
    argument: str
    revision: int = 0


class Critique(ContractModel):
    viable: bool
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class ThesisResult(ContractModel):
    topic: str = Field(min_length=1)
    statement: str
    argument: str
    viability: Critique
    sources: list[Source] = Field(default_factory=list)
    revisions: int = 0


class ResearchRequest(ContractModel):
    topic: str = Field(min_length=1)


class ResearchResponse(ContractModel):
    findings: ResearchFindings


class SynthesisRequest(ContractModel):
    findings: ResearchFindings
    critique: Critique | None = None
    revision: int = 0


class SynthesisResponse(ContractModel):
    draft: ThesisDraft


class CritiqueRequest(ContractModel):
    draft: ThesisDraft
    findings: ResearchFindings


class CritiqueResponse(ContractModel):
    critique: Critique
