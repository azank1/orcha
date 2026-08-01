"""Unit tests for ChecklistStep extensions and _bind_step_to_call."""

from __future__ import annotations

from superagent.graph.state import ChecklistStep, TaskChecklist
from superagent.nodes.execute_agent_calls import _bind_step_to_call

# ---------------------------------------------------------------------------
# ChecklistStep dataclass — new fields default to None
# ---------------------------------------------------------------------------


def test_checklist_step_defaults():
    step = ChecklistStep(step_id="s1", description="Do something")
    assert step.call_id is None
    assert step.tool_name_resolved is None
    assert step.started_at is None
    assert step.completed_at is None
    assert step.status == "pending"
    assert step.agent_id is None


def test_checklist_step_explicit_new_fields():
    step = ChecklistStep(
        step_id="s2",
        description="Do something else",
        call_id="c-123",
        tool_name_resolved="my_agent__run",
        started_at="2026-01-01T00:00:00+00:00",
        completed_at="2026-01-01T00:01:00+00:00",
    )
    assert step.call_id == "c-123"
    assert step.tool_name_resolved == "my_agent__run"
    assert step.started_at == "2026-01-01T00:00:00+00:00"
    assert step.completed_at == "2026-01-01T00:01:00+00:00"


# ---------------------------------------------------------------------------
# _bind_step_to_call — None checklist is a no-op
# ---------------------------------------------------------------------------


def test_bind_step_none_checklist():
    _bind_step_to_call(None, "tool_name", "call-1", "agent-1")


# ---------------------------------------------------------------------------
# _bind_step_to_call — exact agent_id match
# ---------------------------------------------------------------------------


def _make_checklist(*steps: ChecklistStep) -> TaskChecklist:
    return TaskChecklist(
        checklist_id="cl-1",
        goal="Test goal",
        steps=list(steps),
    )


def test_bind_step_matches_by_agent_id():
    step = ChecklistStep(step_id="s1", description="Call agent", agent_id="my-agent")
    cl = _make_checklist(step)
    _bind_step_to_call(cl, "my-agent__tool", "call-42", "my-agent")
    assert step.call_id == "call-42"
    assert step.tool_name_resolved == "my-agent__tool"
    assert step.status == "in_progress"
    assert step.started_at is not None


def test_bind_step_greedy_first_fit_when_no_agent_id():
    s1 = ChecklistStep(step_id="s1", description="Unbound step")
    s2 = ChecklistStep(step_id="s2", description="Another unbound step")
    cl = _make_checklist(s1, s2)
    _bind_step_to_call(cl, "some_tool", "call-1", "agent-x")
    assert s1.call_id == "call-1"
    assert s2.call_id is None  # greedy — only first match is stamped


def test_bind_step_skips_already_bound():
    s1 = ChecklistStep(step_id="s1", description="Already bound", call_id="old-call")
    s2 = ChecklistStep(step_id="s2", description="Unbound")
    cl = _make_checklist(s1, s2)
    _bind_step_to_call(cl, "some_tool", "new-call", "agent-x")
    assert s1.call_id == "old-call"  # unchanged
    assert s2.call_id == "new-call"  # bound now


def test_bind_step_skips_done_steps():
    done_step = ChecklistStep(step_id="s1", description="Done", status="done")
    pending = ChecklistStep(step_id="s2", description="Pending")
    cl = _make_checklist(done_step, pending)
    _bind_step_to_call(cl, "tool", "c-1", "agent")
    assert done_step.call_id is None
    assert pending.call_id == "c-1"


def test_bind_step_skips_failed_steps():
    failed = ChecklistStep(step_id="s1", description="Failed", status="failed")
    pending = ChecklistStep(step_id="s2", description="Pending")
    cl = _make_checklist(failed, pending)
    _bind_step_to_call(cl, "tool", "c-1", "agent")
    assert failed.call_id is None
    assert pending.call_id == "c-1"


def test_bind_step_no_match_leaves_steps_unchanged():
    step = ChecklistStep(
        step_id="s1",
        description="For specific agent",
        agent_id="other-agent",
    )
    cl = _make_checklist(step)
    _bind_step_to_call(cl, "unrelated_tool", "c-1", "different-agent")
    assert step.call_id is None


def test_bind_step_sets_agent_id_when_unbound():
    step = ChecklistStep(step_id="s1", description="Unbound")
    cl = _make_checklist(step)
    _bind_step_to_call(cl, "some_tool", "c-1", "resolved-agent")
    assert step.agent_id == "resolved-agent"


def test_bind_step_only_binds_first_matching():
    s1 = ChecklistStep(step_id="s1", description="First", agent_id="my-agent")
    s2 = ChecklistStep(step_id="s2", description="Second", agent_id="my-agent")
    cl = _make_checklist(s1, s2)
    _bind_step_to_call(cl, "my-agent__run", "c-1", "my-agent")
    assert s1.call_id == "c-1"
    assert s2.call_id is None  # not bound — only first match wins
