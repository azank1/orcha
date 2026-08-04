"""execute_dag_plan node (Slice 1).

Drives an active DAG plan: marks the previous call's result, picks the next
ready node, and issues it as a synthetic tool call — dispatched by the
existing execute_agent_calls node, so every plan step gets the full
ExecutionMiddleware pipeline (verification, settlement, checklist, SSE).
v1 is sequential: one plan node in flight at a time.
"""

from __future__ import annotations

import copy
import logging
from typing import Any

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from .dag_plan import (
    checklist_for_plan,
    mark_result,
    next_ready_node,
    tool_call_for_node,
)

logger = logging.getLogger(__name__)


async def execute_dag_plan_node(
    state: dict[str, Any], config: RunnableConfig
) -> dict[str, Any]:
    plan = state.get("active_plan")
    if not isinstance(plan, dict) or plan.get("status") != "running":
        return {}

    plan = copy.deepcopy(plan)

    # 1. Record the result of the previously issued call, if any.
    messages = state.get("messages", [])
    if plan["issued"] and messages and isinstance(messages[-1], ToolMessage):
        tm = messages[-1]
        content = tm.content if isinstance(tm.content, str) else str(tm.content)
        plan = mark_result(plan, content, str(tm.tool_call_id))
        if plan["status"] != "running":
            logger.info("execute_dag_plan: plan %s", plan["status"])
            return {"active_plan": plan}

    # 2. Pick the next ready node; none → plan complete.
    node_id = next_ready_node(plan)
    if node_id is None:
        plan["status"] = "completed"
        logger.info("execute_dag_plan: plan %s completed", plan["plan_id"])
        return {"active_plan": plan}

    # 3. Build the synthetic tool call for this node.
    tc = tool_call_for_node(
        plan["nodes"][node_id],
        state.get("pnd_candidates", []),
        plan.get("outputs", {}),
        call_seq=len(plan["issued"]),
    )
    if tc is None:
        plan["nodes"][node_id]["status"] = "failed"
        plan["status"] = "failed"
        logger.warning(
            "execute_dag_plan: node %s not dispatchable — plan aborted", node_id
        )
        return {"active_plan": plan}

    plan["issued"][tc["id"]] = node_id
    plan["nodes"][node_id]["status"] = "in_progress"
    logger.info(
        "execute_dag_plan: dispatching node %s as %s (call %s)",
        node_id,
        tc["name"],
        tc["id"],
    )

    updates: dict[str, Any] = {
        "active_plan": plan,
        "messages": [AIMessage(content="", tool_calls=[tc])],
    }
    if not plan.get("checklist_built"):
        plan["checklist_built"] = True
        updates["task_checklist"] = checklist_for_plan(plan)
    return updates
