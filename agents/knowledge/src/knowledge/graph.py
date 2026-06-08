"""LangGraph graph for the knowledge agent — walking skeleton: a single node."""

import logging
from typing import TypedDict

from langgraph.graph import END, START, StateGraph, CompiledStateGraph

logger = logging.getLogger(__name__)

AGENT_NAME = "knowledge"


class State(TypedDict):
    name: str


class Context(TypedDict):
    name: str


def _identify(state: State, context: Context) -> State:
    logger.info("agent '%s' handled a request with context '%s'", state["name"], context["name"])
    return state


def build_graph() -> CompiledStateGraph:
    builder = StateGraph(State, Context)
    builder.add_node("identify", _identify)
    builder.add_edge(START, "identify")
    builder.add_edge("identify", END)
    return builder.compile()
