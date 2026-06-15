"""Unit tests for the three-tier PnD gate."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import HumanMessage
from superagent.graph.state import ChecklistStep, TaskChecklist
from superagent.pnd.gate import pnd_gate


def _state_with_message(text: str) -> dict:
    return {"messages": [HumanMessage(content=text)], "task_checklist": None}


def _make_small_llm(answer: str) -> AsyncMock:
    choice = MagicMock()
    choice.message.content = answer
    resp = MagicMock()
    resp.choices = [choice]
    mock = AsyncMock()
    mock.chat.completions.create = AsyncMock(return_value=resp)
    return mock


# ── Tier 1a ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_tier1a_active_checklist_always_true():
    checklist = TaskChecklist(
        checklist_id="c1",
        goal="Send emails",
        steps=[
            ChecklistStep(step_id="s1", description="Fetch inbox", status="pending"),
        ],
    )
    state = {"messages": [HumanMessage(content="hi")], "task_checklist": checklist}
    result = await pnd_gate(state, _make_small_llm("NO"), "haiku")
    assert result is True


# ── Tier 1b (no-tool) ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_tier1b_conversational_false():
    state = _state_with_message("What is the capital of France?")
    result = await pnd_gate(state, _make_small_llm("NO"), "haiku")
    assert result is False


@pytest.mark.asyncio
async def test_tier1b_hello_false():
    state = _state_with_message("Hello, how are you?")
    result = await pnd_gate(state, _make_small_llm("NO"), "haiku")
    assert result is False


# ── Tier 1c (tool verb) ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_tier1c_send_email_true():
    state = _state_with_message("Send an email to alice@example.com")
    result = await pnd_gate(state, _make_small_llm("NO"), "haiku")
    assert result is True


@pytest.mark.asyncio
async def test_tier1c_fetch_emails_true():
    state = _state_with_message("Fetch my unread emails from Gmail")
    result = await pnd_gate(state, _make_small_llm("NO"), "haiku")
    assert result is True


@pytest.mark.asyncio
async def test_tier1c_search_true():
    state = _state_with_message("Search for flights to Tokyo")
    result = await pnd_gate(state, _make_small_llm("NO"), "haiku")
    assert result is True


# ── Empty state ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_empty_messages_false():
    state = {"messages": [], "task_checklist": None}
    result = await pnd_gate(state, _make_small_llm("YES"), "haiku")
    assert result is False
