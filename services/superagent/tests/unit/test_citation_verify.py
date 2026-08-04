"""Tests for the FR-4.3 citation-presence rule in _structural_verify."""

from __future__ import annotations

import json

from superagent.middleware.pipeline import _structural_verify

RULEBOOK_AGENT = "did:orcha:agent:rulebook-rag"
OTHER_AGENT = "did:orcha:agent:web-scraper"


def _cited_output() -> str:
    return json.dumps(
        {
            "answer": "Answer composed from seeded rulebook passages.",
            "citations": [
                {
                    "chunk_id": "chunk-1",
                    "source_title": "transaction-monitoring",
                    "excerpt": "Any single M2M transaction with a value of GBP 10,000...",
                }
            ],
            "verified": True,
        }
    )


def test_rulebook_output_with_citations_passes():
    verified, reason = _structural_verify(_cited_output(), False, RULEBOOK_AGENT)
    assert verified is True
    assert reason == "ok"


def test_rulebook_output_with_empty_citations_fails():
    content = json.dumps({"answer": "guessed", "citations": [], "verified": False})
    verified, reason = _structural_verify(content, False, RULEBOOK_AGENT)
    assert verified is False
    assert reason == "missing citations"


def test_rulebook_output_without_citations_key_fails():
    content = json.dumps({"answer": "no citation structure at all"})
    verified, reason = _structural_verify(content, False, RULEBOOK_AGENT)
    assert verified is False
    assert reason == "missing citations"


def test_rulebook_output_non_json_fails():
    verified, reason = _structural_verify(
        "The threshold is GBP 10,000, trust me.", False, RULEBOOK_AGENT
    )
    assert verified is False
    assert reason == "missing citations"


def test_rulebook_citation_missing_a_field_fails():
    content = json.dumps(
        {
            "answer": "partial citations",
            "citations": [
                {"chunk_id": "chunk-1", "source_title": "agent-registration"}
            ],
        }
    )
    verified, reason = _structural_verify(content, False, RULEBOOK_AGENT)
    assert verified is False
    assert reason == "missing citations"


def test_rulebook_error_output_still_reports_error():
    verified, reason = _structural_verify("Error: boom", False, RULEBOOK_AGENT)
    assert verified is False
    assert reason == "Error: boom"


def test_rulebook_empty_output_still_reports_empty():
    verified, reason = _structural_verify("", False, RULEBOOK_AGENT)
    assert verified is False
    assert reason == "empty output"


def test_other_agents_unaffected_without_citations():
    verified, reason = _structural_verify("plain text answer", False, OTHER_AGENT)
    assert verified is True
    assert reason == "ok"


def test_other_agents_unaffected_default_agent_id():
    verified, reason = _structural_verify("plain text answer", False)
    assert verified is True
    assert reason == "ok"


def test_other_agents_canvas_still_verified():
    verified, reason = _structural_verify("canvas envelope", True, OTHER_AGENT)
    assert verified is True
    assert reason == "canvas output verified"
