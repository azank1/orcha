"""E2E test — single conversational turn (no PnD, no tool calls)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessageChunk
from superagent.graph.runner import SessionRunner


@pytest.mark.asyncio
async def test_single_conversational_turn(memory_graph):
    runner = SessionRunner(memory_graph)
    session_id = "e2e-single-001"

    mock_chat = MagicMock()

    async def fake_astream(*_a, **_kw):
        yield AIMessageChunk(content="Paris is the capital of France.")

    mock_chat.astream = fake_astream
    mock_chat.bind_tools = MagicMock(return_value=mock_chat)

    import superagent.nodes as _nodes_pkg

    _nodes_pkg._registry["pnd_client"] = AsyncMock()

    with (
        patch("superagent.nodes.orchestrator.ChatOpenAI", return_value=mock_chat),
        patch("superagent.nodes.orchestrator.pnd_gate", return_value=False),
    ):
        events = [
            e
            async for e in runner.run_turn(
                session_id, "u1", "What is the capital of France?"
            )
        ]

    token_events = [e for e in events if e["type"] == "token"]
    done_events = [e for e in events if e["type"] == "done"]
    assert len(done_events) == 1
    assert any("Paris" in e.get("content", "") for e in token_events)
