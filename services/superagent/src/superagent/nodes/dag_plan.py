"""DAG plan state helpers (Slice 1).

Pure functions over a plain-dict plan state (msgpack-safe for Redis
checkpoints). The execute_dag_plan node (Task 6) drives these; they exist
separately so the traversal/IO/naming logic is unit-testable without a graph.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from ..graph.state import ChecklistStep, TaskChecklist
from ..pnd.models import PlanEdge, PlanNode, WorkflowPlan

logger = logging.getLogger(__name__)

_INVALID_TOOL_CHAR_RE = re.compile(r"[^a-zA-Z0-9_-]")
_OUTPUT_REF_RE = re.compile(
    r"^\$tasks\.([A-Za-z0-9_-]+)\.output(?:\.([A-Za-z0-9_]+))?$"
)
_ERROR_PREFIXES = ("Error:", "Input error:", "Unsupported protocol:")


class PlanGraphError(Exception):
    """Plan cannot be executed (cycle, unsupported node type) — fall back to ReAct."""


def _sanitise(agent_id: str) -> str:
    return _INVALID_TOOL_CHAR_RE.sub("_", agent_id)


def _cand_get(candidate: Any, key: str, default: Any = None) -> Any:
    if isinstance(candidate, dict):
        return candidate.get(key, default)
    return getattr(candidate, key, default)


def topo_order(nodes: list[PlanNode], edges: list[PlanEdge]) -> list[str]:
    """Kahn's algorithm over node.dependencies ∪ in-edges. Raises on cycle."""
    deps: dict[str, set[str]] = {n.id: set(n.dependencies) for n in nodes}
    for e in edges:
        if e.target in deps:
            deps[e.target].add(e.source)

    order: list[str] = []
    remaining = dict(deps)
    while remaining:
        ready = [nid for nid, d in remaining.items() if not d]
        if not ready:
            raise PlanGraphError("plan graph has a cycle — cannot topologically sort")
        for nid in ready:
            order.append(nid)
            del remaining[nid]
        for d in remaining.values():
            d.difference_update(ready)
    return order


def new_active_plan(workflow: WorkflowPlan, query: str) -> dict[str, Any]:
    """Build the JSON-safe active_plan state dict from a WorkflowPlan.

    Raises PlanGraphError for anything v1 cannot execute (router nodes, cycles).
    """
    for n in workflow.nodes:
        if n.type == "router":
            raise PlanGraphError(
                "plan contains a router node — conditional branches unsupported in v1"
            )
        if n.type not in ("standard", "system_tool", "human_input"):
            raise PlanGraphError(f"unsupported plan node type: {n.type!r}")

    order = topo_order(workflow.nodes, workflow.edges)
    # Edges carry dependencies too — merge them in so next_ready_node gates on
    # the same dep set topo_order sorted by (edge-only deps would be skipped).
    edge_deps: dict[str, set[str]] = {}
    for e in workflow.edges:
        edge_deps.setdefault(e.target, set()).add(e.source)
    return {
        "plan_id": workflow.id,
        "query": query,
        "status": "running",
        "nodes": {
            n.id: {
                "status": "pending",
                "type": n.type,
                "agent_id": n.agent_id,
                "capability_id": (n.capability or {}).get("capability_id"),
                "description": n.description,
                "dependencies": sorted(
                    set(n.dependencies) | edge_deps.get(n.id, set())
                ),
                "inputs": dict((n.task or {}).get("inputs") or {}),
            }
            for n in workflow.nodes
        },
        "order": order,
        "issued": {},
        "outputs": {},
        "checklist_built": False,
    }


def next_ready_node(plan: dict[str, Any]) -> str | None:
    """First node (in topo order) that is pending with all dependencies done."""
    nodes = plan["nodes"]
    for nid in plan["order"]:
        node = nodes[nid]
        if node["status"] != "pending":
            continue
        if all(nodes[dep]["status"] == "done" for dep in node["dependencies"]):
            return nid
    return None


def resolve_inputs(inputs: dict[str, Any], outputs: dict[str, str]) -> dict[str, Any]:
    """Substitute $tasks.<id>.output[.<field>] refs from prior node outputs.

    Whole-output refs substitute the raw content string. Field refs parse the
    output as JSON and extract the field; unresolvable refs leave the key unset.
    """
    resolved: dict[str, Any] = {}
    for key, value in inputs.items():
        if not isinstance(value, str):
            resolved[key] = value
            continue
        m = _OUTPUT_REF_RE.match(value)
        if not m:
            resolved[key] = value
            continue
        ref_id, field = m.group(1), m.group(2)
        raw = outputs.get(ref_id)
        if raw is None:
            continue
        if field is None:
            resolved[key] = raw
            continue
        try:
            parsed = json.loads(raw)
            resolved[key] = parsed[field]
        except (json.JSONDecodeError, KeyError, TypeError):
            logger.debug(
                "dag_plan: could not resolve %s from node %s output", key, ref_id
            )
    return resolved


def tool_call_for_node(
    node: dict[str, Any],
    candidates: list[Any],
    outputs: dict[str, str],
    call_seq: int,
) -> dict | None:
    """Build a synthetic tool call for a plan node, using the same naming
    conventions the orchestrator uses (_candidates_to_tools):
    MCP → {sanitised_agent_id}__{capability_id}; other protocols → delegate__{id}.

    Returns None if the node's agent is not among the PnD candidates.
    """
    agent_id = node.get("agent_id")
    if not agent_id:
        return None
    candidate = next(
        (c for c in candidates if _cand_get(c, "agent_id") == agent_id), None
    )
    if candidate is None:
        logger.warning("dag_plan: plan agent %s not in pnd_candidates", agent_id)
        return None

    protocol = _cand_get(candidate, "protocol_type", "")
    if protocol == "MCP":
        capability_id = node.get("capability_id")
        if not capability_id:
            caps = _cand_get(candidate, "capabilities", []) or []
            tool_caps = [c for c in caps if _cand_get(c, "capability_type") == "TOOL"]
            capability_id = (
                _cand_get(tool_caps[0], "capability_id") if tool_caps else None
            )
        if not capability_id:
            return None
        name = f"{_sanitise(agent_id)}__{capability_id}"
        args = resolve_inputs(node.get("inputs") or {}, outputs)
    else:
        name = f"delegate__{_sanitise(agent_id)}"
        args = {"task": node.get("description") or ""}

    return {
        "name": name,
        "args": args,
        "id": f"plan_call_{call_seq}",
        "type": "tool_call",
    }


def mark_result(plan: dict[str, Any], content: str, call_id: str) -> dict[str, Any]:
    """Record a finished call's result. Any failure fails the whole plan —
    remaining nodes are abandoned and the orchestrator synthesizes the partial."""
    node_id = plan["issued"].get(call_id)
    if node_id is None:
        logger.warning("dag_plan: result for unknown call_id %s", call_id)
        return plan
    node = plan["nodes"][node_id]
    if content.startswith(_ERROR_PREFIXES):
        node["status"] = "failed"
        node["result_summary"] = content[:200]
        plan["status"] = "failed"
        logger.info("dag_plan: node %s failed — plan aborted: %.120s", node_id, content)
    else:
        node["status"] = "done"
        node["result_summary"] = content[:200]
        plan["outputs"][node_id] = content
    return plan


def checklist_for_plan(plan: dict[str, Any]) -> TaskChecklist:
    """One ChecklistStep per plan node so the CanvasKit progress UX works."""
    return TaskChecklist(
        checklist_id=f"plan-{plan['plan_id']}",
        goal=plan["query"],
        steps=[
            ChecklistStep(
                step_id=nid,
                description=plan["nodes"][nid]["description"],
                agent_id=plan["nodes"][nid]["agent_id"],
            )
            for nid in plan["order"]
        ],
    )
