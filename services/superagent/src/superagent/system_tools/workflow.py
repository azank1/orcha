"""Workflow system tools — save_as_workflow_template."""

from __future__ import annotations

from typing import Any

from ..graph.state import CapturedWorkflow
from .registry import SystemToolRegistry, SystemToolSpec


async def _save_as_workflow_template(
    args: dict[str, Any], state: dict[str, Any]
) -> dict[str, Any]:
    name = args["name"]
    checklist = state.get("task_checklist")

    steps: list[dict[str, Any]] = []
    agents_used: list[str] = []

    if checklist is not None:
        for step in getattr(checklist, "steps", []):
            steps.append(
                {
                    "description": getattr(step, "description", ""),
                    "agent_id": getattr(step, "agent_id", None),
                    "status_at_capture": getattr(step, "status", "done"),
                }
            )
            agent_id = getattr(step, "agent_id", None)
            if agent_id and agent_id not in agents_used:
                agents_used.append(agent_id)

    captured = CapturedWorkflow(
        name=name,
        goal_template=getattr(checklist, "goal", args.get("goal", name))
        if checklist
        else name,
        steps=steps,
        agents_used=agents_used,
        parameters=args.get("parameters", {}),
    )
    state["captured_workflow"] = captured

    return {
        "saved": name,
        "steps": len(steps),
        "agents_used": agents_used,
        "note": "Workflow template captured. It will be persisted at session end.",
    }


def register_workflow_tools(registry: SystemToolRegistry) -> None:
    registry.register(
        SystemToolSpec(
            name="save_as_workflow_template",
            description=(
                "Save the current completed checklist as a reusable workflow template "
                "that can be scheduled or re-run later."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Human-readable template name",
                    },
                    "description": {"type": "string"},
                    "goal": {
                        "type": "string",
                        "description": "Goal template (supports {parameters})",
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Default parameter values",
                    },
                },
                "required": ["name"],
            },
            handler=_save_as_workflow_template,
        )
    )
