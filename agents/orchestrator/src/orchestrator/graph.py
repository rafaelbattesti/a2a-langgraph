"""LangGraph graph for the orchestrator agent — walking skeleton: a single node."""

import logging
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

logger = logging.getLogger(__name__)

AGENT_NAME = "orchestrator"


class State(TypedDict):
    name: str


def _identify(state: State) -> State:
    logger.info("agent '%s' handled a request", state["name"])
    return state


def build_graph():
    builder = StateGraph(State)
    builder.add_node("identify", _identify)
    builder.add_edge(START, "identify")
    builder.add_edge("identify", END)
    return builder.compile()
