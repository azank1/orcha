"""E2E test — 3-step checklist created and updated across turns."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessageChunk
from superagent.graph.runner import SessionRunner


@pytest.mark.asyncio
async def test_checklist_created_turn1(memory_graph):
    """Turn 1: LLM calls create_checklist system tool."""
    runner = SessionRunner(memory_graph)
    session_id = "e2e-mt-001"

    call_count = 0
    mock_chat = MagicMock()

    async def fake_astream(*_a, **_kw):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            yield AIMessageChunk(
                content="",
                tool_calls=[
                    {
                        "name": "create_checklist",
                        "id": "call_tc1",
                        "args": {
                            "goal": "Weekly report",
                            "steps": ["A", "B", "C"],
                        },
                        "type": "tool_call",
                    }
                ],
            )
        else:
            yield AIMessageChunk(
                content="Checklist created! I'll start working through the steps."
            )

    mock_chat.astream = fake_astream
    mock_chat.bind_tools = MagicMock(return_value=mock_chat)

    import superagent.nodes as _nodes_pkg

    _nodes_pkg._registry["pnd_client"] = AsyncMock()

    with (
        patch("superagent.nodes.orchestrator.ChatOpenAI", return_value=mock_chat),
        patch("superagent.nodes.orchestrator.pnd_gate", return_value=False),
    ):
        _ = [
            e
            async for e in runner.run_turn(
                session_id, "u1", "Help me send my weekly email report"
            )
        ]

    # Check state has checklist
    config = {"configurable": {"thread_id": session_id}}
    snapshot = await memory_graph.aget_state(config)
    checklist = snapshot.values.get("task_checklist")
    assert checklist is not None
    assert checklist.goal == "Weekly report"
    assert len(checklist.steps) == 3
