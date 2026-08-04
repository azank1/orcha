"""Unit tests for DAG plan state helpers."""

from __future__ import annotations

import pytest
from superagent.nodes.dag_plan import (
    PlanGraphError,
    checklist_for_plan,
    mark_result,
    new_active_plan,
    next_ready_node,
    resolve_inputs,
    tool_call_for_node,
    topo_order,
)
from superagent.pnd.models import PlanEdge, PlanNode, WorkflowPlan


def _node(
    nid: str,
    agent: str = "did:orcha:agent:a",
    deps: list[str] | None = None,
    ntype: str = "standard",
    inputs: dict | None = None,
    capability_id: str = "search",
) -> PlanNode:
    return PlanNode(
        id=nid,
        type=ntype,
        agent_id=agent,
        description=f"desc {nid}",
        dependencies=deps or [],
        capability={"capability_id": capability_id, "type": "TOOL"}
        if capability_id
        else None,
        task={
            "description": f"desc {nid}",
            "inputs": inputs or {},
            "unresolved_inputs": [],
        },
    )


def _workflow(
    nodes: list[PlanNode], edges: list[PlanEdge] | None = None
) -> WorkflowPlan:
    return WorkflowPlan(
        id="wf-1", nodes=nodes, edges=edges or [], entry_node_id=nodes[0].id
    )


_MCP_CANDIDATE = {
    "agent_id": "did:orcha:agent:a",
    "agent_name": "Agent A",
    "agent_description": "does a",
    "protocol_type": "MCP",
    "relevance_score": 0.9,
    "capabilities": [
        {
            "capability_id": "search",
            "capability_type": "TOOL",
            "name": "search",
            "description": "search",
            "input_schema": None,
            "output_schema": None,
        }
    ],
    "health_status": "HEALTHY",
}

_A2A_CANDIDATE = {
    "agent_id": "did:orcha:agent:b",
    "agent_name": "Agent B",
    "agent_description": "does b",
    "protocol_type": "A2A",
    "relevance_score": 0.8,
    "capabilities": [],
    "health_status": "HEALTHY",
}


class TestTopoOrder:
    def test_linear_chain(self):
        nodes = [_node("n1"), _node("n2", deps=["n1"]), _node("n3", deps=["n2"])]
        assert topo_order(nodes, []) == ["n1", "n2", "n3"]

    def test_edges_add_dependencies(self):
        nodes = [_node("n1"), _node("n2")]
        edges = [PlanEdge(source="n1", target="n2")]
        assert topo_order(nodes, edges) == ["n1", "n2"]

    def test_cycle_raises(self):
        nodes = [_node("n1", deps=["n2"]), _node("n2", deps=["n1"])]
        with pytest.raises(PlanGraphError, match="cycle"):
            topo_order(nodes, [])


class TestNewActivePlan:
    def test_builds_json_safe_state(self):
        import json

        plan = new_active_plan(
            _workflow(
                [_node("n1"), _node("n2", agent="did:orcha:agent:b", deps=["n1"])]
            ),
            "q",
        )
        json.dumps(plan)  # must not raise
        assert plan["status"] == "running"
        assert plan["order"] == ["n1", "n2"]
        assert plan["nodes"]["n1"]["status"] == "pending"
        assert plan["checklist_built"] is False

    def test_router_node_rejected(self):
        with pytest.raises(PlanGraphError, match="router"):
            new_active_plan(_workflow([_node("n1", ntype="router")]), "q")


class TestResolveInputs:
    def test_whole_output_ref(self):
        out = resolve_inputs({"data": "$tasks.n1.output"}, {"n1": "hello"})
        assert out == {"data": "hello"}

    def test_field_ref_from_json_output(self):
        out = resolve_inputs({"v": "$tasks.n1.output.total"}, {"n1": '{"total": 42}'})
        assert out == {"v": 42}

    def test_unresolvable_field_left_unset(self):
        out = resolve_inputs({"v": "$tasks.n1.output.missing"}, {"n1": '{"total": 42}'})
        assert "v" not in out

    def test_literal_values_pass_through(self):
        assert resolve_inputs({"x": 5}, {}) == {"x": 5}


class TestNextReadyNode:
    def test_first_pending_with_deps_done(self):
        plan = new_active_plan(_workflow([_node("n1"), _node("n2", deps=["n1"])]), "q")
        assert next_ready_node(plan) == "n1"
        plan["nodes"]["n1"]["status"] = "done"
        assert next_ready_node(plan) == "n2"
        plan["nodes"]["n2"]["status"] = "done"
        assert next_ready_node(plan) is None

    def test_edge_only_dependency_gates_readiness(self):
        nodes = [_node("n1"), _node("n2")]
        edges = [PlanEdge(source="n1", target="n2")]
        plan = new_active_plan(_workflow(nodes, edges), "q")
        plan["nodes"]["n1"]["status"] = "in_progress"
        # n2 depends on n1 via edge only — must NOT be ready while n1 runs
        assert next_ready_node(plan) is None
        plan["nodes"]["n1"]["status"] = "done"
        assert next_ready_node(plan) == "n2"


class TestToolCallForNode:
    def test_mcp_tool_naming_and_args(self):
        node = new_active_plan(_workflow([_node("n1")]), "q")["nodes"]["n1"]
        tc = tool_call_for_node(node, [_MCP_CANDIDATE], {}, call_seq=0)
        assert tc["name"] == "did_orcha_agent_a__search"
        assert tc["args"] == {}
        assert tc["id"] == "plan_call_0"
        assert tc["type"] == "tool_call"

    def test_a2a_delegate_naming(self):
        node = new_active_plan(
            _workflow([_node("n1", agent="did:orcha:agent:b", capability_id=None)]), "q"
        )["nodes"]["n1"]
        tc = tool_call_for_node(node, [_A2A_CANDIDATE], {}, call_seq=1)
        assert tc["name"] == "delegate__did_orcha_agent_b"
        assert tc["args"] == {"task": "desc n1"}

    def test_unknown_agent_returns_none(self):
        node = new_active_plan(
            _workflow([_node("n1", agent="did:orcha:agent:missing")]), "q"
        )["nodes"]["n1"]
        assert tool_call_for_node(node, [_MCP_CANDIDATE], {}, call_seq=0) is None

    def test_inputs_resolved_into_mcp_args(self):
        node = new_active_plan(
            _workflow([_node("n1", inputs={"q": "$tasks.n0.output"})]), "q"
        )["nodes"]["n1"]
        tc = tool_call_for_node(
            node, [_MCP_CANDIDATE], {"n0": "leads-data"}, call_seq=2
        )
        assert tc["args"] == {"q": "leads-data"}


class TestMarkResult:
    def test_success_marks_done_and_records_output(self):
        plan = new_active_plan(_workflow([_node("n1")]), "q")
        plan["issued"]["plan_call_0"] = "n1"
        plan["nodes"]["n1"]["status"] = "in_progress"
        plan = mark_result(plan, "result payload", "plan_call_0")
        assert plan["nodes"]["n1"]["status"] == "done"
        assert plan["outputs"]["n1"] == "result payload"
        assert plan["status"] == "running"

    def test_error_content_fails_whole_plan(self):
        plan = new_active_plan(_workflow([_node("n1"), _node("n2", deps=["n1"])]), "q")
        plan["issued"]["plan_call_0"] = "n1"
        plan["nodes"]["n1"]["status"] = "in_progress"
        plan = mark_result(plan, "Error: agent exploded", "plan_call_0")
        assert plan["nodes"]["n1"]["status"] == "failed"
        assert plan["status"] == "failed"


class TestChecklistForPlan:
    def test_one_step_per_node(self):
        plan = new_active_plan(
            _workflow([_node("n1"), _node("n2", deps=["n1"])]), "the goal"
        )
        cl = checklist_for_plan(plan)
        assert cl.goal == "the goal"
        assert [s.step_id for s in cl.steps] == ["n1", "n2"]
        assert all(s.status == "pending" for s in cl.steps)
        assert cl.steps[0].agent_id == "did:orcha:agent:a"
