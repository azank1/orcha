"""Checklist system tools — create, update, add steps, abandon."""

from __future__ import annotations

import hashlib
import uuid
from typing import Any

from ..graph.state import ChecklistStep, TaskChecklist
from .registry import SystemToolRegistry, SystemToolSpec


async def _create_checklist(
    args: dict[str, Any], state: dict[str, Any]
) -> dict[str, Any]:
    goal = args["goal"]
    raw_steps = args.get("steps", [])
    checklist_id = str(uuid.uuid4())
    scope_hash = hashlib.sha256(goal.encode()).hexdigest()[:16]
    steps = [
        ChecklistStep(
            step_id=str(uuid.uuid4()),
            description=s if isinstance(s, str) else s.get("description", str(s)),
        )
        for s in raw_steps
    ]
    checklist = TaskChecklist(
        checklist_id=checklist_id,
        goal=goal,
        steps=steps,
        scope_hash=scope_hash,
    )
    # State mutation happens via return value — caller stores it
    state["task_checklist"] = checklist
    return {
        "checklist_id": checklist_id,
        "goal": goal,
        "steps": [s.description for s in steps],
        "status": "created",
    }


async def _update_checklist_step(
    args: dict[str, Any], state: dict[str, Any]
) -> dict[str, Any]:
    checklist: TaskChecklist | None = state.get("task_checklist")
    if checklist is None:
        return {"error": "No active checklist"}
    step_id = args.get("step_id")
    description = args.get("description")
    new_status = args.get("status", "done")
    result_summary = args.get("result_summary", "")
    for step in checklist.steps:
        if step.step_id == step_id or step.description == description:
            step.status = new_status
            if result_summary:
                step.result_summary = result_summary
            return {"updated": step.step_id, "status": new_status}
    return {"error": f"Step not found: {step_id or description}"}


async def _add_checklist_step(
    args: dict[str, Any], state: dict[str, Any]
) -> dict[str, Any]:
    checklist: TaskChecklist | None = state.get("task_checklist")
    if checklist is None:
        return {"error": "No active checklist"}
    description = args["description"]
    step = ChecklistStep(step_id=str(uuid.uuid4()), description=description)
    checklist.steps.append(step)
    return {"added": step.step_id, "description": description}


async def _abandon_checklist(
    args: dict[str, Any], state: dict[str, Any]
) -> dict[str, Any]:
    checklist: TaskChecklist | None = state.get("task_checklist")
    if checklist is None:
        return {"error": "No active checklist"}
    reason = args.get("reason", "")
    checklist_id = checklist.checklist_id
    state["task_checklist"] = None
    return {"abandoned": checklist_id, "reason": reason}


def register_checklist_tools(registry: SystemToolRegistry) -> None:
    registry.register(
        SystemToolSpec(
            name="create_checklist",
            description=(
                "Create a task checklist to track a multi-step goal. "
                "Call this when the user asks for something requiring multiple agent actions."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "goal": {"type": "string", "description": "The overall goal"},
                    "steps": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of step descriptions",
                    },
                },
                "required": ["goal"],
            },
            handler=_create_checklist,
        )
    )
    registry.register(
        SystemToolSpec(
            name="update_checklist_step",
            description="Mark a checklist step as done, failed, or in_progress.",
            parameters={
                "type": "object",
                "properties": {
                    "step_id": {"type": "string"},
                    "description": {
                        "type": "string",
                        "description": "Step description (alternative to step_id)",
                    },
                    "status": {
                        "type": "string",
                        "enum": ["pending", "in_progress", "done", "failed"],
                    },
                    "result_summary": {"type": "string"},
                },
            },
            handler=_update_checklist_step,
        )
    )
    registry.register(
        SystemToolSpec(
            name="add_checklist_step",
            description="Add a new step to the active checklist.",
            parameters={
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                },
                "required": ["description"],
            },
            handler=_add_checklist_step,
        )
    )
    registry.register(
        SystemToolSpec(
            name="abandon_checklist",
            description="Abandon the active checklist (e.g. user changed their mind).",
            parameters={
                "type": "object",
                "properties": {
                    "reason": {"type": "string"},
                },
            },
            handler=_abandon_checklist,
        )
    )
