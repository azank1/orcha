"""In-memory Google OAuth tokens keyed by opaque session/user key (from gateway state)."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import threading
import time
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class GoogleTokens:
    access_token: str
    refresh_token: str | None = None
    expires_at: float | None = None  # monotonic timestamp

    def is_expired(self, buffer_seconds: float = 120) -> bool:
        if self.expires_at is None:
            return False
        return time.monotonic() >= self.expires_at - buffer_seconds


_lock = threading.Lock()
_store: dict[str, GoogleTokens] = {}


def put_tokens(key: str, access_token: str, refresh_token: str | None, expires_in: int | None) -> None:
    exp: float | None = None
    if expires_in is not None:
        exp = time.monotonic() + float(expires_in)
    with _lock:
        _store[key] = GoogleTokens(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=exp,
        )
    logger.info(
        "oauth_tokens_put key=%s has_refresh=%s expires_in=%s store_size=%d",
        key,
        bool(refresh_token),
        expires_in,
        len(_store),
    )


def get_tokens(key: str) -> GoogleTokens | None:
    with _lock:
        tok = _store.get(key)
    logger.info("oauth_tokens_get key=%s hit=%s", key, tok is not None)
    return tok


def clear_tokens(key: str) -> None:
    with _lock:
        _store.pop(key, None)


def snapshot_keys() -> list[str]:
    with _lock:
        return list(_store.keys())
