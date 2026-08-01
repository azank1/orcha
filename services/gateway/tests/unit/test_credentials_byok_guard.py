"""Unit tests for the BYOK base_url SSRF guard on POST /api/v1/credentials."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-32-bytes-1234567")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("SUPERAGENT_URL", "http://127.0.0.1:8001")
os.environ.setdefault("REGISTRY_URL", "http://127.0.0.1:8003")


@pytest_asyncio.fixture
async def client_with_mocks():
    from gateway.auth.jwt import create_access_token
    from gateway.main import app

    redis = AsyncMock()
    redis.sismember = AsyncMock(return_value=False)
    redis.get = AsyncMock(return_value="user-001")

    app.state.redis = redis
    app.state.superagent = AsyncMock()

    token, _ = create_access_token(user_id="user-001", email="test@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac, redis, headers


def _byok_base_url_payload(value: str) -> dict:
    return {
        "agent_id": "__llm__",
        "var_name": "base_url",
        "value": value,
        "scope": "session",
        "session_id": "sess-123",
    }


@pytest.mark.parametrize(
    "value",
    [
        "http://localhost:11434",
        "http://127.0.0.1:8000",
        "https://10.0.0.1/x",
        "https://172.16.0.5/v1",
        "https://192.168.1.10/v1",
        "https://169.254.169.254/latest/meta-data",
        "https://0.0.0.0:8000",
        "https://sandbox-registry:8000",
        "https://metadata.google.internal/v1",
        "https://ollama.local:11434",
        "not-a-url",
    ],
)
async def test_byok_base_url_rejects_internal_hosts(client_with_mocks, value):
    ac, redis, headers = client_with_mocks

    resp = await ac.post(
        "/api/v1/credentials", json=_byok_base_url_payload(value), headers=headers
    )

    assert resp.status_code == 400
    assert resp.json()["detail"]
    redis.set.assert_not_awaited()


async def test_byok_base_url_allows_public_https(client_with_mocks):
    ac, redis, headers = client_with_mocks

    resp = await ac.post(
        "/api/v1/credentials",
        json=_byok_base_url_payload("https://api.groq.com/openai/v1"),
        headers=headers,
    )

    assert resp.status_code == 204
    redis.set.assert_awaited_once_with(
        "gateway:creds:session:sess-123:__llm__:base_url",
        "https://api.groq.com/openai/v1",
        ex=3600,
    )


async def test_byok_non_base_url_vars_skip_validation(client_with_mocks):
    ac, redis, headers = client_with_mocks

    resp = await ac.post(
        "/api/v1/credentials",
        json={
            "agent_id": "__llm__",
            "var_name": "api_key",
            "value": "anything-goes",
            "scope": "session",
            "session_id": "sess-123",
        },
        headers=headers,
    )

    assert resp.status_code == 204
    redis.set.assert_awaited_once()


async def test_other_agents_base_url_skips_validation(client_with_mocks):
    ac, redis, headers = client_with_mocks

    resp = await ac.post(
        "/api/v1/credentials",
        json={
            "agent_id": "did:orcha:agent:some-agent",
            "var_name": "base_url",
            "value": "http://localhost:11434",
            "scope": "session",
            "session_id": "sess-123",
        },
        headers=headers,
    )

    assert resp.status_code == 204
    redis.set.assert_awaited_once()
