"""Unit tests for respond_node CDV stop-reason message (flag-gated)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage
from superagent.nodes import respond as respond_mod


@pytest.mark.asyncio
async def test_stopper_halt_with_empty_reply_emits_reason(monkeypatch):
    monkeypatch.setattr(
        respond_mod, "settings", MagicMock(cdv_verification_enabled=True)
    )
    monkeypatch.setattr(
        "superagent.verification.cdv_integration.stopper_should_stop",
        lambda state: True,
    )
    state = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[{"name": "a__search", "args": {}, "id": "call-1"}],
            )
        ]
    }
    result = await respond_mod.respond_node(state)
    assert len(result["messages"]) == 1
    assert "verification guard" in result["messages"][0].content


@pytest.mark.asyncio
async def test_flag_off_keeps_stock_passthrough(monkeypatch):
    monkeypatch.setattr(
        respond_mod, "settings", MagicMock(cdv_verification_enabled=False)
    )
    state = {"messages": [AIMessage(content="")]}
    result = await respond_mod.respond_node(state)
    assert result == {}
