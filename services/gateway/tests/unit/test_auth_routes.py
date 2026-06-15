"""Unit tests for auth routes (register, login, refresh, logout)."""

from __future__ import annotations

import hashlib
import os
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-32-bytes-1234567")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("SUPERAGENT_URL", "http://127.0.0.1:8001")
os.environ.setdefault("REGISTRY_URL", "http://127.0.0.1:8003")


def _make_user(
    *,
    id: str = "user-001",
    email: str = "test@example.com",
    password_hash: str | None = None,
    is_active: bool = True,
) -> MagicMock:
    user = MagicMock()
    user.id = id
    user.email = email
    user.is_active = is_active
    if password_hash is None:
        import bcrypt

        password_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode()
    user.password_hash = password_hash
    user.is_dev_mode = False
    return user


def _make_refresh_record(
    *,
    id: str = "rt-001",
    user_id: str = "user-001",
    raw_token: str | None = None,
    revoked: bool = False,
    expired: bool = False,
) -> MagicMock:
    if raw_token is None:
        raw_token = str(uuid.uuid4())
    record = MagicMock()
    record.id = id
    record.user_id = user_id
    record.token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    record.revoked = revoked
    now = datetime.now(UTC)
    record.expires_at = now - timedelta(days=1) if expired else now + timedelta(days=30)
    return record, raw_token


@pytest_asyncio.fixture
async def client_with_mocks():
    from gateway.main import app

    db = AsyncMock()
    db.user = AsyncMock()
    db.refreshtoken = AsyncMock()
    db.workflowtemplate = AsyncMock()

    redis = AsyncMock()
    redis.sismember = AsyncMock(return_value=False)
    redis.sadd = AsyncMock()
    redis.expire = AsyncMock()

    app.state.db = db
    app.state.redis = redis
    app.state.superagent = AsyncMock()
    app.state.registry = AsyncMock()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac, db, redis


# ── Register ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_success(client_with_mocks):
    ac, db, redis = client_with_mocks
    db.user.find_unique = AsyncMock(return_value=None)
    db.user.create = AsyncMock(return_value=_make_user())
    db.refreshtoken.create = AsyncMock(return_value=MagicMock())

    resp = await ac.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client_with_mocks):
    ac, db, redis = client_with_mocks
    db.user.find_unique = AsyncMock(return_value=_make_user())

    resp = await ac.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


# ── Login ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_login_success(client_with_mocks):
    ac, db, redis = client_with_mocks
    db.user.find_unique = AsyncMock(return_value=_make_user())
    db.refreshtoken.create = AsyncMock(return_value=MagicMock())

    resp = await ac.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client_with_mocks):
    ac, db, redis = client_with_mocks
    db.user.find_unique = AsyncMock(return_value=_make_user())

    resp = await ac.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_user(client_with_mocks):
    ac, db, redis = client_with_mocks
    db.user.find_unique = AsyncMock(return_value=None)

    resp = await ac.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "password123"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user(client_with_mocks):
    ac, db, redis = client_with_mocks
    db.user.find_unique = AsyncMock(return_value=_make_user(is_active=False))

    resp = await ac.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert resp.status_code == 403


# ── Refresh ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_refresh_valid_token(client_with_mocks):
    ac, db, redis = client_with_mocks
    record, raw_token = _make_refresh_record()
    db.refreshtoken.find_unique = AsyncMock(return_value=record)
    db.refreshtoken.update = AsyncMock(return_value=record)
    db.user.find_unique = AsyncMock(return_value=_make_user(id=record.user_id))
    db.refreshtoken.create = AsyncMock(return_value=MagicMock())

    resp = await ac.post("/auth/refresh", json={"refresh_token": raw_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_refresh_revoked_token(client_with_mocks):
    ac, db, redis = client_with_mocks
    record, raw_token = _make_refresh_record(revoked=True)
    db.refreshtoken.find_unique = AsyncMock(return_value=record)

    resp = await ac.post("/auth/refresh", json={"refresh_token": raw_token})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_expired_token(client_with_mocks):
    ac, db, redis = client_with_mocks
    record, raw_token = _make_refresh_record(expired=True)
    db.refreshtoken.find_unique = AsyncMock(return_value=record)

    resp = await ac.post("/auth/refresh", json={"refresh_token": raw_token})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_unknown_token(client_with_mocks):
    ac, db, redis = client_with_mocks
    db.refreshtoken.find_unique = AsyncMock(return_value=None)

    resp = await ac.post("/auth/refresh", json={"refresh_token": str(uuid.uuid4())})
    assert resp.status_code == 401


# ── Logout ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_logout_adds_jti_to_revoked(client_with_mocks):
    ac, db, redis = client_with_mocks
    db.refreshtoken.update_many = AsyncMock(return_value=MagicMock())

    # Get a valid access token first
    db.user.find_unique = AsyncMock(return_value=_make_user())
    db.refreshtoken.create = AsyncMock(return_value=MagicMock())
    login_resp = await ac.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    access_token = login_resp.json()["access_token"]

    resp = await ac.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 204
    redis.sadd.assert_called_once()
    args = redis.sadd.call_args[0]
    assert args[0] == "jwt:revoked"
