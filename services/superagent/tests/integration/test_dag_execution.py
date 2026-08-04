"""Integration tests: DAG-routed goal executes plan nodes through the graph."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from superagent.pnd.client import PlanUnavailableError
from superagent.pnd.models import PlanResponse

# The plan's agent_id mirrors the conftest gmail_candidate so tool_call_for_node
# finds it among the fetched PnD candidates.
_PLAN_JSON = {
    "success": True,
    "message": "ok",
    "workflow": {
        "id": "wf-test",
        "entry_node_id": "n1",
        "metadata": {},
        "nodes": [
            {
                "id": "n1",
                "type": "standard",
                "agent_id": "did:orcha:agent:gmail-mcp-001",
                "description": "Search emails",
                "dependencies": [],
                "config": {},
                "capability": {"capability_id": "list_emails", "type": "TOOL"},
                "task": {
                    "description": "Search emails",
                    "inputs": {"max_results": 5},
                    "unresolved_inputs": [],
                },
                "unresolved_inputs": [],
            }
        ],
        "edges": [],
    },
}

# gmail_candidate agent_id sanitised + capability (see dag_plan.tool_call_for_node;
# the sanitiser replaces ':' but keeps '-').
_EXPECTED_TOOL = "did_orcha_agent_gmail-mcp-001__list_emails"

# 2+ step markers ("first ", " then ") → Channel A score 0.30; with the patched
# dag_route_high=0.30 the goal routes to the DAG planner without Channel B.
_GOAL = (
    "First search my inbox for unread invoice emails, "
    "and then summarise what you find into a short report"
)

_MW_RESULT = {"content": "Found 3 emails about invoices", "base_fee": "0"}


@pytest.fixture
def dag_pnd_client(mock_pnd_client):
    mock_pnd_client.get_plan = AsyncMock(
        return_value=PlanResponse.model_validate(_PLAN_JSON)
    )
    return mock_pnd_client


def _make_synthesis_chat(text: str) -> MagicMock:
    """Mock ChatOpenAI whose stream yields one plain chunk (no tool calls)."""
    mock_chat = MagicMock()

    async def fake_astream(*_a, **_kw):
        yield AIMessageChunk(content=text)

    mock_chat.astream = fake_astream
    mock_chat.bind_tools = MagicMock(return_value=mock_chat)
    return mock_chat


def _dag_settings_patches():
    """Patch settings in both modules that read the DAG flags."""
    router_settings = patch("superagent.routing.goal_router.settings")
    orch_settings = patch("superagent.nodes.orchestrator.settings")
    return router_settings, orch_settings


def _step_id(step: Any) -> Any:
    return (
        getattr(step, "step_id", None)
        if not isinstance(step, dict)
        else step["step_id"]
    )


class TestDagExecution:
    @pytest.mark.asyncio
    async def test_dag_goal_executes_plan_node_and_synthesizes(
        self, memory_graph, session_state, dag_pnd_client, monkeypatch
    ):
        import superagent.nodes as _nodes_pkg

        _nodes_pkg._registry["pnd_client"] = dag_pnd_client
        config = {"configurable": {"thread_id": "dag-test-1"}}

        executed: list[dict[str, Any]] = []

        async def fake_execute(self, **kwargs: Any) -> dict[str, Any]:
            executed.append(kwargs)
            return _MW_RESULT

        monkeypatch.setattr(
            "superagent.middleware.pipeline.ExecutionMiddleware.execute", fake_execute
        )

        router_patch, orch_patch = _dag_settings_patches()
        with (
            patch(
                "superagent.nodes.orchestrator.ChatOpenAI",
                return_value=_make_synthesis_chat("Workflow complete: found 3 emails."),
            ),
            patch("superagent.nodes.orchestrator.pnd_gate", return_value=True),
            patch(
                "superagent.nodes.orchestrator._get_small_llm",
                return_value=MagicMock(),
            ),
            router_patch as router_settings,
            orch_patch as orch_settings,
        ):
            router_settings.dag_planner_enabled = True
            router_settings.dag_route_high = 0.30
            router_settings.dag_route_low = 0.10
            orch_settings.dag_planner_enabled = True

            state = session_state
            state["messages"] = [HumanMessage(content=_GOAL)]
            final = await memory_graph.ainvoke(state, config)

        # 1. Goal routed to the planner.
        dag_pnd_client.get_plan.assert_awaited_once()

        # 2. The plan node's synthetic tool call was dispatched through the
        #    ExecutionMiddleware pipeline.
        assert [kw["tool_name"] for kw in executed] == [_EXPECTED_TOOL]

        # 3. Plan ran to completion and recorded the node output.
        assert final["active_plan"]["status"] == "completed"
        assert final["active_plan"]["outputs"]["n1"] == "Found 3 emails about invoices"

        # 4. A task checklist with one step per plan node was built.
        checklist = final["task_checklist"]
        assert checklist is not None
        steps = checklist["steps"] if isinstance(checklist, dict) else checklist.steps
        assert [_step_id(s) for s in steps] == ["n1"]

        # 5. The graph ended with the synthesis message on the respond path.
        last = final["messages"][-1]
        assert isinstance(last, AIMessage)
        assert "found 3 emails" in last.content.lower()

    @pytest.mark.asyncio
    async def test_flag_off_never_calls_get_plan(
        self, memory_graph, session_state, dag_pnd_client, monkeypatch
    ):
        """Default settings (dag_planner_enabled=False) — normal ReAct turn."""
        import superagent.nodes as _nodes_pkg

        _nodes_pkg._registry["pnd_client"] = dag_pnd_client
        config = {"configurable": {"thread_id": "dag-test-2"}}

        async def fake_execute(self, **kwargs: Any) -> dict[str, Any]:
            raise AssertionError("no tool call should be dispatched")

        monkeypatch.setattr(
            "superagent.middleware.pipeline.ExecutionMiddleware.execute", fake_execute
        )

        with (
            patch(
                "superagent.nodes.orchestrator.ChatOpenAI",
                return_value=_make_synthesis_chat("Here is your answer."),
            ),
            patch("superagent.nodes.orchestrator.pnd_gate", return_value=True),
        ):
            state = session_state
            state["messages"] = [HumanMessage(content=_GOAL)]
            final = await memory_graph.ainvoke(state, config)

        dag_pnd_client.get_plan.assert_not_called()
        assert final["active_plan"] is None
        last = final["messages"][-1]
        assert isinstance(last, AIMessage)
        assert "answer" in last.content.lower()

    @pytest.mark.asyncio
    async def test_plan_unavailable_falls_back_to_react(
        self, memory_graph, session_state, dag_pnd_client, monkeypatch
    ):
        """get_plan raises PlanUnavailableError → turn completes via ReAct."""
        import superagent.nodes as _nodes_pkg

        dag_pnd_client.get_plan = AsyncMock(side_effect=PlanUnavailableError("boom"))
        _nodes_pkg._registry["pnd_client"] = dag_pnd_client
        config = {"configurable": {"thread_id": "dag-test-3"}}

        async def fake_execute(self, **kwargs: Any) -> dict[str, Any]:
            raise AssertionError("no tool call should be dispatched")

        monkeypatch.setattr(
            "superagent.middleware.pipeline.ExecutionMiddleware.execute", fake_execute
        )

        router_patch, orch_patch = _dag_settings_patches()
        with (
            patch(
                "superagent.nodes.orchestrator.ChatOpenAI",
                return_value=_make_synthesis_chat("ReAct fallback answer."),
            ),
            patch("superagent.nodes.orchestrator.pnd_gate", return_value=True),
            patch(
                "superagent.nodes.orchestrator._get_small_llm",
                return_value=MagicMock(),
            ),
            router_patch as router_settings,
            orch_patch as orch_settings,
        ):
            router_settings.dag_planner_enabled = True
            router_settings.dag_route_high = 0.30
            router_settings.dag_route_low = 0.10
            orch_settings.dag_planner_enabled = True

            state = session_state
            state["messages"] = [HumanMessage(content=_GOAL)]
            final = await memory_graph.ainvoke(state, config)

        dag_pnd_client.get_plan.assert_awaited_once()
        assert final["active_plan"] is None
        last = final["messages"][-1]
        assert isinstance(last, AIMessage)
        assert "fallback" in last.content.lower()
