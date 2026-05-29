"""Deterministic unit tests for pure logic (no network, no LLM)."""

import pytest
from a2a.helpers.proto_helpers import new_data_message, new_text_message
from a2a.types import Role
from google.protobuf.json_format import MessageToDict

from coordinator.graph import _route
from mcp_arxiv import server as mcp_arxiv_server
from researcher.mcp_tools import _coerce
from thesis_common import config
from thesis_common.a2a_payloads import (
    JSON_MEDIA_TYPE,
    PayloadContractError,
    message_from_model,
    model_from_message,
)
from thesis_common.a2a_server import CONTRACT_EXTENSION_URI, build_card
from thesis_common.schemas import (
    CONTRACT_VERSION,
    Critique,
    ResearchRequest,
    ResearchResponse,
    Source,
    SynthesisRequest,
    ThesisResult,
)


def test_coerce_unwraps_mcp_text_blocks():
    blocks = [
        {"type": "text", "text": '{"title": "T", "summary": "S", "url": "U"}', "id": "1"}
    ]
    assert _coerce(blocks) == [{"title": "T", "summary": "S", "url": "U"}]


def test_coerce_passes_through_plain_dicts():
    data = [{"title": "T", "summary": "S", "url": "U"}]
    assert _coerce(data) == data


def test_coerce_handles_garbage():
    assert _coerce("not json") == []
    assert _coerce(None) == []


def test_arxiv_search_returns_empty_when_rate_limited(monkeypatch):
    class RateLimitedClient:
        def results(self, search):
            raise mcp_arxiv_server.arxiv.HTTPError("https://arxiv.example", 5, 429)

    monkeypatch.setattr(mcp_arxiv_server, "_client", RateLimitedClient())

    assert mcp_arxiv_server.arxiv_search("retrieval augmented generation") == []


def test_arxiv_search_raises_unexpected_http_errors(monkeypatch):
    class BadRequestClient:
        def results(self, search):
            raise mcp_arxiv_server.arxiv.HTTPError("https://arxiv.example", 5, 400)

    monkeypatch.setattr(mcp_arxiv_server, "_client", BadRequestClient())

    with pytest.raises(mcp_arxiv_server.arxiv.HTTPError):
        mcp_arxiv_server.arxiv_search("bad query")


def test_route_finalizes_when_viable():
    state = {"critique": {"viable": True, "issues": [], "suggestions": []}, "revisions": 0}
    assert _route(state) == "finalize"


def test_route_revises_under_budget(monkeypatch):
    monkeypatch.setattr(config, "MAX_REVISIONS", 2)
    state = {"critique": {"viable": False, "issues": ["x"], "suggestions": []}, "revisions": 1}
    assert _route(state) == "synthesize"


def test_route_finalizes_at_budget(monkeypatch):
    monkeypatch.setattr(config, "MAX_REVISIONS", 2)
    state = {"critique": {"viable": False, "issues": ["x"], "suggestions": []}, "revisions": 2}
    assert _route(state) == "finalize"


def test_thesis_result_roundtrips():
    result = ThesisResult(
        topic="t",
        statement="s",
        argument="a",
        viability=Critique(viable=True),
        sources=[Source(title="T", summary="S", url="U")],
        revisions=1,
    )
    assert ThesisResult(**result.model_dump()) == result


def test_a2a_data_part_roundtrips_typed_payload():
    payload = ResearchRequest(topic="efficient RAG for code")
    message = message_from_model(payload, role=Role.ROLE_USER)

    assert model_from_message(message, ResearchRequest) == payload


def test_a2a_text_part_payload_is_rejected():
    message = new_text_message('{"topic": "efficient RAG"}', role=Role.ROLE_USER)

    with pytest.raises(PayloadContractError, match="data part"):
        model_from_message(message, ResearchRequest)


def test_malformed_synthesis_payload_fails_before_graph_execution():
    message = new_data_message({"topic": "efficient RAG"}, role=Role.ROLE_USER)

    with pytest.raises(PayloadContractError, match="Invalid SynthesisRequest"):
        model_from_message(message, SynthesisRequest)


def test_agent_card_advertises_payload_contracts():
    card = build_card(
        name="Researcher",
        description="Gathers evidence.",
        skill_id="gather_evidence",
        public_url="http://agent_researcher:8080",
        input_model=ResearchRequest,
        output_model=ResearchResponse,
    )

    skill = card.skills[0]
    extension = card.capabilities.extensions[0]
    params = MessageToDict(extension.params)

    assert card.default_input_modes == [JSON_MEDIA_TYPE]
    assert card.default_output_modes == [JSON_MEDIA_TYPE]
    assert skill.input_modes == [JSON_MEDIA_TYPE]
    assert skill.output_modes == [JSON_MEDIA_TYPE]
    assert f"contract:{CONTRACT_VERSION}" in skill.tags
    assert "input:ResearchRequest" in skill.tags
    assert "output:ResearchResponse" in skill.tags
    assert extension.uri == CONTRACT_EXTENSION_URI
    assert params["input_schema"] == "ResearchRequest"
    assert params["output_schema"] == "ResearchResponse"
    assert params["contract_version"] == CONTRACT_VERSION
