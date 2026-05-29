"""Coordinator LangGraph: orchestrates the specialist agents over A2A.

Flow: research (once) -> [ synthesize -> critique ]*  with a bounded refine loop.
The loop repeats while the Critic rejects viability and revisions < MAX_REVISIONS.
"""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from thesis_common import config
from thesis_common.a2a_client import call_agent
from thesis_common.schemas import (
    Critique,
    CritiqueRequest,
    CritiqueResponse,
    ResearchFindings,
    ResearchRequest,
    ResearchResponse,
    SynthesisRequest,
    SynthesisResponse,
    ThesisDraft,
    ThesisResult,
)


class CoordState(TypedDict, total=False):
    topic: str
    findings: dict
    draft: dict
    critique: dict
    revisions: int
    result: dict


async def _research(state: CoordState) -> dict:
    response = await call_agent(
        config.RESEARCHER_URL,
        ResearchRequest(topic=state["topic"]),
        ResearchResponse,
    )
    return {"findings": response.findings.model_dump()}


async def _synthesize(state: CoordState) -> dict:
    critique = Critique(**state["critique"]) if state.get("critique") else None
    payload = SynthesisRequest(
        topic=state["topic"],
        findings=ResearchFindings(**state["findings"]),
        critique=critique,
        revision=state.get("revisions", 0),
    )
    response = await call_agent(config.SYNTHESIZER_URL, payload, SynthesisResponse)
    return {"draft": response.draft.model_dump()}


async def _critique(state: CoordState) -> dict:
    payload = CritiqueRequest(
        topic=state["topic"],
        draft=ThesisDraft(**state["draft"]),
        findings=ResearchFindings(**state["findings"]),
    )
    response = await call_agent(config.CRITIC_URL, payload, CritiqueResponse)
    return {
        "critique": response.critique.model_dump(),
        "revisions": state.get("revisions", 0) + 1,
    }


def _route(state: CoordState) -> str:
    critique = Critique(**state["critique"])
    if critique.viable or state["revisions"] >= config.MAX_REVISIONS:
        return "finalize"
    return "synthesize"


async def _finalize(state: CoordState) -> dict:
    findings = ResearchFindings(**state["findings"])
    draft = ThesisDraft(**state["draft"])
    critique = Critique(**state["critique"])
    result = ThesisResult(
        topic=state["topic"],
        statement=draft.statement,
        argument=draft.argument,
        viability=critique,
        sources=findings.sources,
        revisions=state["revisions"],
    )
    return {"result": result.model_dump()}


def build_graph():
    graph = StateGraph(CoordState)
    graph.add_node("research", _research)
    graph.add_node("synthesize", _synthesize)
    graph.add_node("critique", _critique)
    graph.add_node("finalize", _finalize)
    graph.add_edge(START, "research")
    graph.add_edge("research", "synthesize")
    graph.add_edge("synthesize", "critique")
    graph.add_conditional_edges(
        "critique", _route, {"synthesize": "synthesize", "finalize": "finalize"}
    )
    graph.add_edge("finalize", END)
    return graph.compile()
