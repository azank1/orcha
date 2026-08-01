"""Unit tests for checklist system tools."""

from __future__ import annotations

import pytest
from superagent.graph.state import default_state
from superagent.system_tools.checklist import (
    _abandon_checklist,
    _add_checklist_step,
    _create_checklist,
    _update_checklist_step,
)


@pytest.fixture
def state():
    return default_state("s1", "u1")


@pytest.mark.asyncio
async def test_create_checklist(state):
    result = await _create_checklist(
        {"goal": "Send weekly report", "steps": ["Fetch data", "Format", "Send"]},
        state,
    )
    assert result["status"] == "created"
    assert len(result["steps"]) == 3
    checklist = state["task_checklist"]
    assert checklist.goal == "Send weekly report"
    assert len(checklist.steps) == 3


@pytest.mark.asyncio
async def test_update_step_by_description(state):
    await _create_checklist({"goal": "Task", "steps": ["Step A", "Step B"]}, state)
    result = await _update_checklist_step(
        {"description": "Step A", "status": "done", "result_summary": "Done OK"},
        state,
    )
    assert "updated" in result
    step = state["task_checklist"].steps[0]
    assert step.status == "done"
    assert step.result_summary == "Done OK"


@pytest.mark.asyncio
async def test_update_missing_step_returns_error(state):
    await _create_checklist({"goal": "Task", "steps": ["A"]}, state)
    result = await _update_checklist_step({"description": "nonexistent"}, state)
    assert "error" in result


@pytest.mark.asyncio
async def test_add_step(state):
    await _create_checklist({"goal": "Task", "steps": ["A"]}, state)
    result = await _add_checklist_step({"description": "New step"}, state)
    assert "added" in result
    assert len(state["task_checklist"].steps) == 2


@pytest.mark.asyncio
async def test_abandon_checklist(state):
    await _create_checklist({"goal": "Task", "steps": ["A"]}, state)
    result = await _abandon_checklist({"reason": "user cancelled"}, state)
    assert "abandoned" in result
    assert state["task_checklist"] is None


@pytest.mark.asyncio
async def test_update_without_checklist_returns_error(state):
    result = await _update_checklist_step({"description": "x"}, state)
    assert "error" in result


@pytest.mark.asyncio
async def test_scope_hash_set_on_create(state):
    await _create_checklist({"goal": "My goal"}, state)
    assert state["task_checklist"].scope_hash != ""
