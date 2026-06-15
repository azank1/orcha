"""E2E test — save_as_workflow_template captures completed checklist."""

from __future__ import annotations

import pytest
from superagent.graph.state import ChecklistStep, TaskChecklist, default_state
from superagent.system_tools.workflow import _save_as_workflow_template


@pytest.mark.asyncio
async def test_save_workflow_captures_checklist():
    state = default_state("s1", "u1")
    state["task_checklist"] = TaskChecklist(
        checklist_id="c1",
        goal="Send weekly report",
        steps=[
            ChecklistStep(
                "s1", "Fetch data", "done", agent_id="did:emerge:agent:data-001"
            ),
            ChecklistStep(
                "s2", "Send email", "done", agent_id="did:emerge:agent:gmail-001"
            ),
        ],
    )

    result = await _save_as_workflow_template(
        {"name": "Weekly Report Workflow", "description": "Auto-generated"},
        state,
    )

    assert result["saved"] == "Weekly Report Workflow"
    assert result["steps"] == 2
    assert "did:emerge:agent:data-001" in result["agents_used"]
    assert "did:emerge:agent:gmail-001" in result["agents_used"]

    captured = state["captured_workflow"]
    assert captured is not None
    assert captured.name == "Weekly Report Workflow"
    assert len(captured.steps) == 2


@pytest.mark.asyncio
async def test_save_workflow_without_checklist():
    state = default_state("s1", "u1")
    result = await _save_as_workflow_template(
        {"name": "Empty Workflow", "goal": "Do something"},
        state,
    )
    assert result["steps"] == 0
    assert state["captured_workflow"] is not None
