"""AgentCard definition for the analysis agent (JSONRPC interface only)."""

import os

from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from a2a.utils.constants import TransportProtocol

_BASE_URL = os.environ.get("AGENT_URL", "http://localhost:9003")
_RPC_PATH = "/a2a/jsonrpc"


def build_card() -> AgentCard:
    skill = AgentSkill(
        id="analyze-corpus",
        name="Analyze Corpus",
        description="Analyzes the corpus and elicits parameters when needed.",
        tags=["analysis", "elicitation"],
    )
    return AgentCard(
        name="analysis",
        description="Analyzes the corpus and elicits parameters via input-required.",
        version="0.0.0",
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=True),
        supported_interfaces=[
            AgentInterface(
                protocol_binding=TransportProtocol.JSONRPC.value,
                url=f"{_BASE_URL}{_RPC_PATH}",
            ),
        ],
        skills=[skill],
    )
