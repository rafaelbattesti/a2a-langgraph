"""A2A entrypoint for the Researcher agent."""

from __future__ import annotations

from thesis_common import config
from thesis_common.a2a_server import build_card, serve

from .graph import build_graph

_graph = build_graph()


async def handle(payload: dict) -> dict:
    result = await _graph.ainvoke({"topic": payload["topic"]})
    return result["findings"]


def main() -> None:
    card = build_card(
        name="Researcher",
        description="Gathers arXiv evidence via MCP and synthesizes research findings.",
        skill_id="gather_evidence",
        public_url=config.PUBLIC_URL,
    )
    serve(card, handle)
