"""AgentCard definition for the knowledge agent (JSONRPC interface only)."""

import os

from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from a2a.utils.constants import TransportProtocol

_BASE_URL = os.environ.get("AGENT_URL", "http://localhost:9002")
_RPC_PATH = "/a2a/jsonrpc"


def build_card() -> AgentCard:
    skill = AgentSkill(
        id="rag-and-publish",
        name="RAG and Publish",
        description="Retrieves from the corpus, synthesizes a cited artifact, and publishes.",
        tags=["rag", "retrieval", "publish"],
    )
    return AgentCard(
        name="knowledge",
        description="Performs RAG over the corpus and synthesizes cited artifacts.",
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
