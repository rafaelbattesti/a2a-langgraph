"""Deterministic unit tests for pure logic (no network, no LLM)."""

from coordinator.graph import _route
from researcher.mcp_tools import _coerce
from thesis_common import config
from thesis_common.schemas import Critique, Source, ThesisResult


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
