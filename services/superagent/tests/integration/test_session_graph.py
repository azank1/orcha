"""Integration tests — state persists across turns via MemorySaver."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessageChunk
from superagent.graph.runner import SessionRunner


@pytest.mark.asyncio
async def test_multi_turn_state_accumulates(memory_graph):
    """Messages accumulate across turns in the same session."""
    runner = SessionRunner(memory_graph)
    session_id = "test-mt-001"
    user_id = "u1"

    mock_chat = MagicMock()

    async def fake_astream(*_a, **_kw):
        yield AIMessageChunk(content="Hello there!")

    mock_chat.astream = fake_astream
    mock_chat.bind_tools = MagicMock(return_value=mock_chat)

    import superagent.nodes as _nodes_pkg

    _nodes_pkg._registry["pnd_client"] = AsyncMock()

    with (
        patch("superagent.nodes.orchestrator.ChatOpenAI", return_value=mock_chat),
        patch("superagent.nodes.orchestrator.pnd_gate", return_value=False),
    ):
        events_turn1 = [e async for e in runner.run_turn(session_id, user_id, "Hi")]

    assert any(e["type"] == "done" for e in events_turn1)

    async def fake_astream2(*_a, **_kw):
        yield AIMessageChunk(content="How can I help?")

    mock_chat.astream = fake_astream2

    with (
        patch("superagent.nodes.orchestrator.ChatOpenAI", return_value=mock_chat),
        patch("superagent.nodes.orchestrator.pnd_gate", return_value=False),
    ):
        events_turn2 = [
            e async for e in runner.run_turn(session_id, user_id, "What can you do?")
        ]

    assert any(e["type"] == "done" for e in events_turn2)

    # Check snapshot has accumulated messages
    config = {"configurable": {"thread_id": session_id}}
    snapshot = await memory_graph.aget_state(config)
    messages = snapshot.values.get("messages", [])
    # 2 human + 2 AI = at least 4 messages
    assert len(messages) >= 4
