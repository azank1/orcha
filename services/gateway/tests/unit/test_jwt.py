"""Unit tests for JWT helpers."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-32-bytes-1234567")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("SUPERAGENT_URL", "http://127.0.0.1:8001")
os.environ.setdefault("REGISTRY_URL", "http://127.0.0.1:8003")

from gateway.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
)


def test_access_token_round_trip():
    token, jti = create_access_token(user_id="user-123", email="user@example.com")
    payload = decode_access_token(token)
    assert payload.user_id == "user-123"
    assert payload.email == "user@example.com"
    assert payload.jti == jti


def test_access_token_jti_unique():
    _, jti1 = create_access_token("u1", "a@b.com")
    _, jti2 = create_access_token("u1", "a@b.com")
    assert jti1 != jti2


def test_tampered_token_raises():
    token, _ = create_access_token("user-1", "x@x.com")
    tampered = token[:-4] + "XXXX"
    with pytest.raises(ValueError, match="Invalid token"):
        decode_access_token(tampered)


def test_wrong_type_token_raises():
    """A token with type != 'access' should be rejected."""
    import uuid
    from datetime import UTC, datetime, timedelta

    from jose import jwt

    from gateway.config import settings

    payload = {
        "sub": "user-1",
        "email": "x@x.com",
        "jti": str(uuid.uuid4()),
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(days=1),
        "type": "refresh",  # wrong type
    }
    token = jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    with pytest.raises(ValueError, match="Not an access token"):
        decode_access_token(token)


def test_refresh_token_raw_and_hash_differ():
    raw, token_hash = create_refresh_token()
    assert raw != token_hash
    assert len(token_hash) == 64  # sha256 hex digest


def test_refresh_tokens_are_unique():
    raw1, hash1 = create_refresh_token()
    raw2, hash2 = create_refresh_token()
    assert raw1 != raw2
    assert hash1 != hash2
