"""AgentCard definition for the orchestrator agent (JSONRPC interface only)."""

import os

from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from a2a.utils.constants import TransportProtocol

_BASE_URL = os.environ.get("AGENT_URL", "http://localhost:9001")
_RPC_PATH = "/a2a/jsonrpc"
_REST_PREFIX = "/a2a/rest"


def build_card() -> AgentCard:
    skill = AgentSkill(
        id="classify-and-dispatch",
        name="Classify and Dispatch",
        description="Classifies user intent and dispatches to the appropriate agent.",
        tags=["routing", "classification"],
    )
    return AgentCard(
        name="orchestrator",
        description="Classifies intent and dispatches requests to specialized agents.",
        version="0.0.0",
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=True),
        supported_interfaces=[
            AgentInterface(
                protocol_binding=TransportProtocol.JSONRPC.value,
                url=f"{_BASE_URL}{_RPC_PATH}",
            )
        ],
        skills=[skill],
    )
