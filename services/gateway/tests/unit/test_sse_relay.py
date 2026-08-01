"""Unit tests for SSE relay enrichment logic."""

from __future__ import annotations

from gateway.sessions.sse_relay import _enrich


def test_token_event():
    event = {"type": "token", "content": "Hello"}
    result = _enrich(event, set())
    assert result["event_class"] == "message.ai.token"
    assert result["payload"] is event


def test_invocation_start():
    event = {
        "type": "invocation_start",
        "call_id": "c1",
        "tool_name": "db__query",
        "agent_id": "db",
        "inputs": {"id": 1},
    }
    result = _enrich(event, set())
    assert result["event_class"] == "invocation.start"
    p = result["payload"]
    assert p["call_id"] == "c1"
    assert p["tool_name"] == "db__query"
    assert p["agent_id"] == "db"
    assert p["inputs"] == {"id": 1}
    assert p["capability_id"] == ""
    assert p["protocol"] == ""


def test_invocation_progress():
    event = {
        "type": "invocation_progress",
        "call_id": "c1",
        "status": "working",
        "message": "Agent is processing…",
    }
    result = _enrich(event, set())
    assert result["event_class"] == "invocation.progress"
    p = result["payload"]
    assert p["call_id"] == "c1"
    assert p["status"] == "working"
    assert p["message"] == "Agent is processing…"


def test_invocation_result():
    event = {
        "type": "invocation_result",
        "call_id": "c1",
        "tool_name": "db__query",
        "agent_id": "db",
        "status": "success",
        "content_preview": "{'ok': true}",
    }
    result = _enrich(event, set())
    assert result["event_class"] == "invocation.result"
    p = result["payload"]
    assert p["call_id"] == "c1"
    assert p["status"] == "success"
    assert p["content_preview"] == "{'ok': true}"


def test_agents_discovered():
    event = {"type": "agents_discovered", "agents": []}
    result = _enrich(event, set())
    assert result["event_class"] == "agent.discovered"


def test_token_usage():
    event = {"type": "token_usage", "estimated_token_count": 100}
    result = _enrich(event, set())
    assert result["event_class"] == "session.token_usage"
    p = result["payload"]
    assert p["total_tokens"] == 100
    assert p["input_tokens"] == 0
    assert p["output_tokens"] == 0


def test_artifact_created():
    event = {
        "type": "artifact_created",
        "artifact_id": "a1",
        "description": "Report",
        "mime_type": "text/plain",
    }
    result = _enrich(event, set())
    assert result["event_class"] == "artifact.created"
    p = result["payload"]
    assert p["artifact_id"] == "a1"
    assert p["name"] == "Report"
    assert p["type"] == "text/plain"


def test_interrupt():
    event = {
        "type": "interrupt",
        "interrupt_id": "i1",
        "interrupt_type": "auth",
        "message": "Please provide credentials",
    }
    result = _enrich(event, set())
    assert result["event_class"] == "interrupt.required"
    p = result["payload"]
    assert p["interrupt_id"] == "i1"
    assert p["message"] == "Please provide credentials"
    assert p["prompt"] == "Please provide credentials"


def test_interrupt_falls_back_to_prompt_when_message_missing():
    event = {"type": "interrupt", "interrupt_id": "i2", "prompt": "Legacy prompt"}
    p = _enrich(event, set())["payload"]
    assert p["prompt"] == "Legacy prompt"
    assert p["message"] == "Legacy prompt"


def test_done():
    event = {"type": "done"}
    result = _enrich(event, set())
    assert result["event_class"] == "session.complete"


def test_unknown_type_becomes_raw():
    event = {"type": "some_new_type", "data": "x"}
    result = _enrich(event, set())
    assert result["event_class"] == "raw.some_new_type"


def test_checklist_first_occurrence_is_created():
    seen: set[str] = set()
    event = {"type": "checklist_snapshot", "checklist_id": "cl-1"}
    result = _enrich(event, seen)
    assert result["event_class"] == "checklist.created"
    assert "cl-1" in seen
    assert result["payload"]["tasks"] == []


def test_checklist_payload_normalizes_steps_to_tasks():
    seen: set[str] = set()
    event = {
        "type": "checklist_snapshot",
        "checklist_id": "cl-1",
        "goal": "Ship feature",
        "version": 3,
        "steps": [
            {"step_id": "a", "description": "Build", "status": "in_progress"},
            {"step_id": "b", "description": "Test", "status": "done"},
        ],
    }
    result = _enrich(event, seen)
    assert result["event_class"] == "checklist.created"
    p = result["payload"]
    assert p["checklist_id"] == "cl-1"
    assert p["goal"] == "Ship feature"
    assert p["version"] == 3
    assert p["tasks"] == [
        {"id": "a", "label": "Build", "status": "running"},
        {"id": "b", "label": "Test", "status": "done"},
    ]


def test_checklist_second_occurrence_is_updated():
    seen: set[str] = {"cl-1"}
    event = {"type": "checklist_snapshot", "checklist_id": "cl-1"}
    result = _enrich(event, seen)
    assert result["event_class"] == "checklist.updated"


def test_checklist_different_ids_are_independent():
    seen: set[str] = set()
    e1 = {"type": "checklist_snapshot", "checklist_id": "cl-1"}
    e2 = {"type": "checklist_snapshot", "checklist_id": "cl-2"}
    r1 = _enrich(e1, seen)
    r2 = _enrich(e2, seen)
    assert r1["event_class"] == "checklist.created"
    assert r2["event_class"] == "checklist.created"
    # Second call for cl-1 → updated
    r3 = _enrich(e1, seen)
    assert r3["event_class"] == "checklist.updated"
