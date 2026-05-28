"""A2A entrypoint for the Synthesizer agent."""

from __future__ import annotations

from thesis_common import config
from thesis_common.a2a_server import build_card, serve

from .graph import build_graph

_graph = build_graph()


async def handle(payload: dict) -> dict:
    state = {
        "findings": payload["findings"],
        "critique": payload.get("critique"),
        "revision": payload.get("revision", 0),
    }
    result = await _graph.ainvoke(state)
    return result["draft"]


def main() -> None:
    card = build_card(
        name="Synthesizer",
        description="Composes a thesis statement and reasoned argument from research findings.",
        skill_id="synthesize_thesis",
        public_url=config.PUBLIC_URL,
    )
    serve(card, handle)
