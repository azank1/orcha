"""Integration tests for MCPHandler — all MCP SDK calls mocked."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from superagent.handlers.mcp_handler import MCPHandler

_TRANSPORT_SSE = {"type": "SSE", "endpoint": "http://mock-agent:9000/mcp"}
_TRANSPORT_STDIO = {"type": "STDIO", "command": "python", "args": ["-m", "mock_agent"]}


@pytest.mark.asyncio
async def test_sse_call_returns_text():
    handler = MCPHandler(auth_headers={"Authorization": "Bearer test"})

    mock_result = MagicMock()
    mock_result.content = [MagicMock(text="You have 3 unread emails.")]
    mock_result.content[0].text = "You have 3 unread emails."

    with patch(
        "superagent.handlers.mcp_handler.sse_client",
        new_callable=MagicMock,
    ) as mock_sse:
        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        mock_session.call_tool = AsyncMock(return_value=mock_result)

        cm_outer = AsyncMock()
        cm_outer.__aenter__ = AsyncMock(return_value=(AsyncMock(), AsyncMock()))
        cm_outer.__aexit__ = AsyncMock(return_value=False)
        mock_sse.return_value = cm_outer

        cm_inner = AsyncMock()
        cm_inner.__aenter__ = AsyncMock(return_value=mock_session)
        cm_inner.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "superagent.handlers.mcp_handler.ClientSession", return_value=cm_inner
        ):
            result = await handler.call_tool(
                agent_id="agent-1",
                capability_id="list_emails",
                args={"max_results": 5},
                transport=_TRANSPORT_SSE,
            )

    assert "unread" in str(result)


@pytest.mark.asyncio
async def test_sse_fallback_when_no_sdk():
    """When mcp SDK is not installed, fall back to raw HTTP."""
    handler = MCPHandler(auth_headers={})

    with (
        patch.dict("sys.modules", {"mcp": None, "mcp.client.sse": None}),
        patch("httpx.AsyncClient") as MockClient,
    ):
        instance = MockClient.return_value.__aenter__.return_value
        instance.post = AsyncMock(
            return_value=MagicMock(
                json=lambda: {"content": [{"type": "text", "text": "ok"}]},
                raise_for_status=MagicMock(),
            )
        )
        result = await handler._call_sse_raw(
            "agent-1", "list_emails", {}, _TRANSPORT_SSE
        )
    assert result is not None
