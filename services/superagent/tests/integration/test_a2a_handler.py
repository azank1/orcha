"""Integration tests for A2AHandler — httpx calls mocked via respx."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from superagent.handlers.a2a_handler import A2AHandler, _resume_value_to_text

_TRANSPORT = {"type": "HTTP", "endpoint": "http://mock-a2a:9001"}


def _make_task_state(status: str, result_text: str = "") -> dict:
    task = {
        "id": "task-001",
        "status": {"state": status},
        "artifacts": [],
    }
    if result_text:
        task["artifacts"] = [{"parts": [{"kind": "text", "text": result_text}]}]
    return task


@pytest.mark.asyncio
async def test_happy_path_task_completes():
    handler = A2AHandler(auth_headers={})

    responses = [
        _make_task_state("working"),
        _make_task_state("completed", "Task done: found 5 emails"),
    ]
    call_count = 0

    async def mock_get_task(client, endpoint, task_id):
        nonlocal call_count
        result = responses[min(call_count, len(responses) - 1)]
        call_count += 1
        return result

    with (
        patch("superagent.handlers.a2a_handler.asyncio.sleep", new_callable=AsyncMock),
        patch.object(handler, "_get_task", side_effect=mock_get_task),
        patch("httpx.AsyncClient") as MockClient,
    ):
        instance = MockClient.return_value.__aenter__.return_value
        instance.post = AsyncMock(
            return_value=AsyncMock(
                raise_for_status=lambda: None,
                json=lambda: {"result": {"id": "task-001"}},
            )
        )
        result = await handler.send_task(
            agent_id="did:a2a:agent:001",
            task="List my emails",
            transport=_TRANSPORT,
            state={"user_id": "u1"},
        )

    assert "5 emails" in str(result)


@pytest.mark.asyncio
async def test_failed_task_returns_error():
    handler = A2AHandler(auth_headers={})

    async def mock_get_task(client, endpoint, task_id):
        return _make_task_state("failed")

    with (
        patch("superagent.handlers.a2a_handler.asyncio.sleep", new_callable=AsyncMock),
        patch.object(handler, "_get_task", side_effect=mock_get_task),
        patch("httpx.AsyncClient") as MockClient,
    ):
        instance = MockClient.return_value.__aenter__.return_value
        instance.post = AsyncMock(
            return_value=AsyncMock(
                raise_for_status=lambda: None,
                json=lambda: {"result": {"id": "task-001"}},
            )
        )
        result = await handler.send_task(
            agent_id="did:a2a:agent:001",
            task="Do something",
            transport=_TRANSPORT,
            state={"user_id": "u1"},
        )

    assert "Error" in str(result)


def test_resume_value_to_text_supports_response_payload():
    assert (
        _resume_value_to_text({"status": "complete", "response": "approve this"})
        == "approve this"
    )
    assert _resume_value_to_text({"response": "free-form answer"}) == "free-form answer"
