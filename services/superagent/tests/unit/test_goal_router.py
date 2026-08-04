"""Unit tests for the hybrid goal router (Channel A heuristic + Channel B arbiter)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from superagent.routing.goal_router import (
    classify_channel_b,
    route_goal,
    score_channel_a_heuristic,
)


def _cand(agent_id: str, protocol: str = "MCP") -> dict:
    return {"agent_id": agent_id, "protocol_type": protocol, "capabilities": []}


def _llm_saying(text: str) -> MagicMock:
    llm = MagicMock()
    message = MagicMock(content=text)
    llm.chat.completions.create = AsyncMock(
        return_value=MagicMock(choices=[MagicMock(message=message)])
    )
    return llm


class TestChannelA:
    def test_simple_goal_few_candidates_low_score(self):
        score = score_channel_a_heuristic("search for coffee shops", [_cand("a")])
        assert score <= 0.35

    def test_many_candidates_multi_protocol_steps_high_score(self):
        cands = [_cand(f"a{i}", "MCP" if i % 2 else "A2A") for i in range(5)]
        goal = (
            "First search for leads in fintech, then write them to a CRM, "
            "and then send an outreach email to each one of them"
        )
        score = score_channel_a_heuristic(goal, cands)
        assert score >= 0.75

    def test_score_capped_at_1(self):
        cands = [_cand(f"a{i}", "MCP" if i % 2 else "A2A") for i in range(10)]
        goal = "first do x, then do y, and then do z " * 5
        assert score_channel_a_heuristic(goal, cands) <= 1.0


class TestClassifyChannelB:
    @pytest.mark.asyncio
    async def test_yes_response_true(self):
        assert await classify_channel_b("goal", _llm_saying("YES")) is True

    @pytest.mark.asyncio
    async def test_no_response_false(self):
        assert await classify_channel_b("goal", _llm_saying("NO")) is False


class TestRouteGoal:
    @pytest.mark.asyncio
    async def test_flag_off_always_react(self):
        with patch("superagent.routing.goal_router.settings") as s:
            s.dag_planner_enabled = False
            cands = [_cand(f"a{i}", "MCP" if i % 2 else "A2A") for i in range(5)]
            assert (
                await route_goal("first x, then y, and then z", cands, MagicMock())
                == "react"
            )

    @pytest.mark.asyncio
    async def test_active_checklist_stays_react(self):
        with patch("superagent.routing.goal_router.settings") as s:
            s.dag_planner_enabled = True
            cands = [_cand(f"a{i}", "MCP" if i % 2 else "A2A") for i in range(5)]
            result = await route_goal(
                "first x, then y, and then z", cands, MagicMock(), has_checklist=True
            )
            assert result == "react"

    @pytest.mark.asyncio
    async def test_high_score_routes_dag_without_channel_b(self):
        with patch("superagent.routing.goal_router.settings") as s:
            s.dag_planner_enabled = True
            s.dag_route_high = 0.75
            s.dag_route_low = 0.35
            llm = MagicMock()
            llm.chat.completions.create = AsyncMock(
                side_effect=AssertionError("Channel B must not be called")
            )
            cands = [_cand(f"a{i}", "MCP" if i % 2 else "A2A") for i in range(5)]
            goal = "first search for leads, then write to crm, and then email them all"
            assert await route_goal(goal, cands, llm) == "dag"

    @pytest.mark.asyncio
    async def test_low_score_routes_react(self):
        with patch("superagent.routing.goal_router.settings") as s:
            s.dag_planner_enabled = True
            s.dag_route_high = 0.75
            s.dag_route_low = 0.35
            assert (
                await route_goal("search for coffee shops", [_cand("a")], MagicMock())
                == "react"
            )

    @pytest.mark.asyncio
    async def test_borderline_defers_to_channel_b(self):
        with patch("superagent.routing.goal_router.settings") as s:
            s.dag_planner_enabled = True
            s.dag_route_high = 0.75
            s.dag_route_low = 0.35
            llm = _llm_saying("YES")
            # 2 candidates + one step marker → score ~0.30-0.50 (borderline)
            cands = [_cand("a", "MCP"), _cand("b", "A2A")]
            assert await route_goal("find leads then email them", cands, llm) == "dag"
            llm = _llm_saying("NO")
            assert await route_goal("find leads then email them", cands, llm) == "react"

    @pytest.mark.asyncio
    async def test_channel_b_error_falls_back_to_react(self):
        with patch("superagent.routing.goal_router.settings") as s:
            s.dag_planner_enabled = True
            s.dag_route_high = 0.75
            s.dag_route_low = 0.35
            llm = MagicMock()
            llm.chat.completions.create = AsyncMock(side_effect=RuntimeError("boom"))
            cands = [_cand("a", "MCP"), _cand("b", "A2A")]
            assert await route_goal("find leads then email them", cands, llm) == "react"
