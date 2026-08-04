"""Unit tests for PnDClient.get_plan and plan models."""

from __future__ import annotations

import httpx
import pytest
from superagent.pnd.client import PlanUnavailableError, PnDClient
from superagent.pnd.models import PlanResponse, WorkflowPlan

_PLAN_PAYLOAD = {
    "success": True,
    "message": "Workflow plan generated successfully",
    "workflow": {
        "id": "wf-1",
        "version": "1.0",
        "created_at": "2026-08-03T00:00:00Z",
        "entry_node_id": "n1",
        "validated": True,
        "validation_tier": "deterministic",
        "confidence_score": 0.9,
        "metadata": {"original_query": "q", "node_count": 2, "edge_count": 1},
        "nodes": [
            {
                "id": "n1",
                "type": "standard",
                "agent_id": "did:orcha:agent:search",
                "description": "Search for leads",
                "dependencies": [],
                "config": {},
                "capability": {"capability_id": "search", "type": "TOOL"},
                "task": {
                    "description": "Search for leads",
                    "inputs": {},
                    "unresolved_inputs": [],
                },
                "unresolved_inputs": [],
                "field_mappings": [],
            },
            {
                "id": "n2",
                "type": "standard",
                "agent_id": "did:orcha:agent:crm",
                "description": "Write results",
                "dependencies": ["n1"],
                "config": {},
                "capability": None,
                "task": {
                    "description": "Write $tasks.n1.output to CRM",
                    "inputs": {"data": "$tasks.n1.output"},
                    "unresolved_inputs": [],
                },
                "unresolved_inputs": [],
                "field_mappings": [],
            },
        ],
        "edges": [{"source": "n1", "target": "n2", "condition": None}],
    },
}


def _client_with_response(status_code: int, payload: dict) -> PnDClient:
    client = PnDClient(base_url="http://pnd.test")

    async def _post(url: str, **kwargs):
        assert url == "/api/v1/plan"
        return httpx.Response(
            status_code, json=payload, request=httpx.Request("POST", url)
        )

    client._client = httpx.AsyncClient()
    client._client.post = _post  # type: ignore[method-assign]
    return client


class TestGetPlan:
    @pytest.mark.asyncio
    async def test_happy_path_parses_manifest(self):
        client = _client_with_response(200, _PLAN_PAYLOAD)
        resp = await client.get_plan("find leads and write to CRM")
        assert isinstance(resp, PlanResponse)
        assert resp.success is True
        assert isinstance(resp.workflow, WorkflowPlan)
        assert [n.id for n in resp.workflow.nodes] == ["n1", "n2"]
        assert resp.workflow.nodes[1].dependencies == ["n1"]
        assert resp.workflow.edges[0].source == "n1"

    @pytest.mark.asyncio
    async def test_success_false_raises_plan_unavailable(self):
        client = _client_with_response(
            200,
            {
                "success": False,
                "message": "ambiguous",
                "workflow": _PLAN_PAYLOAD["workflow"],
            },
        )
        with pytest.raises(PlanUnavailableError, match="ambiguous"):
            await client.get_plan("vague goal")

    @pytest.mark.asyncio
    async def test_http_error_raises_plan_unavailable_with_status(self):
        client = _client_with_response(503, {"detail": "no agents"})
        with pytest.raises(PlanUnavailableError) as exc_info:
            await client.get_plan("goal")
        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_malformed_payload_raises_plan_unavailable(self):
        client = _client_with_response(200, {"success": True, "workflow": {"bogus": 1}})
        with pytest.raises(PlanUnavailableError):
            await client.get_plan("goal")


class TestPlanNodeCoercion:
    def test_extra_node_fields_tolerated(self):
        # Upstream manifest nodes carry more fields than we model — must not break parsing.
        resp = PlanResponse.model_validate(_PLAN_PAYLOAD)
        node = resp.workflow.nodes[0]
        assert node.capability == {"capability_id": "search", "type": "TOOL"}
        assert node.task["inputs"] == {}
