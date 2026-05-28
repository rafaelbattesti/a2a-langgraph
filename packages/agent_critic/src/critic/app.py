"""A2A entrypoint for the Critic agent."""

from __future__ import annotations

from thesis_common import config
from thesis_common.a2a_server import build_card, serve

from .graph import build_graph

_graph = build_graph()


async def handle(payload: dict) -> dict:
    state = {"draft": payload["draft"], "findings": payload["findings"]}
    result = await _graph.ainvoke(state)
    return result["critique"]


def main() -> None:
    card = build_card(
        name="Critic",
        description="Judges whether a thesis draft is novel, feasible and well grounded.",
        skill_id="critique_thesis",
        public_url=config.PUBLIC_URL,
    )
    serve(card, handle)
