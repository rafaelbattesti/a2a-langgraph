"""Typed payloads exchanged between thesis agents over A2A data parts (public facade)."""

from contracts import CONTRACT_VERSION

from .models import (
    Critique,
    CritiqueRequest,
    CritiqueResponse,
    ResearchFindings,
    ResearchRequest,
    ResearchResponse,
    Source,
    SynthesisRequest,
    SynthesisResponse,
    ThesisDraft,
    ThesisRequest,
    ThesisResult,
)

__all__ = [
    "CONTRACT_VERSION",
    "Critique",
    "CritiqueRequest",
    "CritiqueResponse",
    "ResearchFindings",
    "ResearchRequest",
    "ResearchResponse",
    "Source",
    "SynthesisRequest",
    "SynthesisResponse",
    "ThesisDraft",
    "ThesisRequest",
    "ThesisResult",
]
