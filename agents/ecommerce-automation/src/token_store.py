"""In-memory Shopify OAuth tokens keyed by SuperAgent session id."""

from __future__ import annotations

from dataclasses import dataclass
import threading
import time


@dataclass
class ShopifyToken:
    access_token: str
    expires_at: float | None = None

    def is_expired(self, buffer_seconds: float = 60) -> bool:
        if self.expires_at is None:
            return False
        return time.monotonic() >= self.expires_at - buffer_seconds


_lock = threading.Lock()
_store: dict[str, ShopifyToken] = {}


def put_token(session_key: str, access_token: str, expires_in: int | None = None) -> None:
    exp: float | None = None
    if isinstance(expires_in, int):
        exp = time.monotonic() + float(expires_in)
    with _lock:
        _store[session_key] = ShopifyToken(access_token=access_token, expires_at=exp)


def get_token(session_key: str) -> ShopifyToken | None:
    with _lock:
        tok = _store.get(session_key)
    if tok and tok.is_expired():
        clear_token(session_key)
        return None
    return tok


def clear_token(session_key: str) -> None:
    with _lock:
        _store.pop(session_key, None)
