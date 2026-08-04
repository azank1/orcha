"""Integration tests for orchestrator_llm_node."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessageChunk, HumanMessage
from superagent.graph.state import default_state


@pytest.mark.asyncio
async def test_conversational_no_pnd_call():
    """For a pure conversational message, PnD should not be called."""
    state = default_state("s1", "u1")
    state["messages"] = [HumanMessage(content="Hello, how are you?")]

    mock_pnd = MagicMock()
    mock_chat = MagicMock()

    async def fake_astream(*_a, **_kw):
        yield AIMessageChunk(content="I'm doing great!")

    mock_chat.astream = fake_astream
    mock_chat.bind_tools = MagicMock(return_value=mock_chat)

    import superagent.nodes as _nodes_pkg

    _nodes_pkg._registry["pnd_client"] = mock_pnd

    with (
        patch("superagent.nodes.orchestrator.ChatOpenAI", return_value=mock_chat),
        patch("superagent.nodes.orchestrator.pnd_gate", return_value=False),
    ):
        from superagent.nodes.orchestrator import orchestrator_llm_node

        result = await orchestrator_llm_node(state, {})

    mock_pnd.get_candidates.assert_not_called()
    assert len(result["messages"]) == 1
    assert "great" in result["messages"][0].content.lower()


@pytest.mark.asyncio
async def test_tool_call_includes_pnd_schemas(mock_pnd_client):
    """When PnD gate fires, tool schemas appear in bind_tools."""
    state = default_state("s1", "u1")
    state["messages"] = [HumanMessage(content="Fetch my emails")]

    captured_tools: list = []
    mock_chat = MagicMock()

    async def fake_astream(*_a, **_kw):
        yield AIMessageChunk(content="Fetching emails…")

    def bind_side(tools, **_kw):
        captured_tools.clear()
        captured_tools.extend(tools)
        return mock_chat

    mock_chat.astream = fake_astream
    mock_chat.bind_tools = MagicMock(side_effect=bind_side)

    import superagent.nodes as _nodes_pkg

    _nodes_pkg._registry["pnd_client"] = mock_pnd_client

    with (
        patch("superagent.nodes.orchestrator.ChatOpenAI", return_value=mock_chat),
        patch("superagent.nodes.orchestrator.pnd_gate", return_value=True),
    ):
        from superagent.nodes.orchestrator import orchestrator_llm_node

        await orchestrator_llm_node(state, {})

    tools = captured_tools
    tool_names = [t["function"]["name"] for t in tools]
    assert any("gmail" in name.lower() or "list_emails" in name for name in tool_names)
