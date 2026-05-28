"""A2A entrypoint for the Coordinator agent (the system's public entry point)."""

from __future__ import annotations

from thesis_common import config
from thesis_common.a2a_server import build_card, serve

from .graph import build_graph

_graph = build_graph()


async def handle(payload: dict) -> dict:
    result = await _graph.ainvoke({"topic": payload["topic"], "revisions": 0})
    return result["result"]


def main() -> None:
    card = build_card(
        name="ThesisCoordinator",
        description="Produces a reasoned, viable research thesis from a topic by orchestrating specialist agents.",
        skill_id="produce_thesis",
        public_url=config.PUBLIC_URL,
    )
    serve(card, handle)
