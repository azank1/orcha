"""
OAuth authentication for authenticated web scraping.

Flow:
1. Agent detects auth is required → returns A2A ``input-required`` with an auth URL.
2. Client opens ``GET /auth/start?provider=google&state=<task_id>``
   → redirects to provider's consent screen.
3. Provider redirects back to ``GET /auth/callback`` with an auth code.
4. Agent exchanges code for tokens, stores them encrypted in-memory,
   and returns HTML that auto-closes the popup window.
5. Subsequent scrape requests for that session can inject the stored
   ``Authorization: Bearer <token>`` header.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlencode

import aiohttp
import structlog
from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from .config import settings

logger = structlog.get_logger()

router = APIRouter(prefix="/auth", tags=["auth"])

# ── Data types ────────────────────────────────────────────────────────────────


@dataclass
class StoredToken:
    """An OAuth token bound to a session + provider."""

    provider: str
    access_token: str
    refresh_token: str | None = None
    expires_at: float | None = None
    scopes: list[str] = field(default_factory=list)


# In-memory store: session_id → {provider → StoredToken}
# MVP only — swap with Redis for production.
_token_store: dict[str, dict[str, StoredToken]] = {}

# Pending auth states — maps CSRF state → (session_id, provider)
_pending_states: dict[str, tuple[str, str]] = {}

# ── Provider configs ──────────────────────────────────────────────────────────

PROVIDERS: dict[str, dict[str, Any]] = {
    "google": {
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes": [
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ],
        "client_id_setting": "google_client_id",
        "client_secret_setting": "google_client_secret",
    },
}

# ── Routes ────────────────────────────────────────────────────────────────────


@router.get("/providers")
async def list_providers():
    """Return which OAuth providers are configured."""
    available = []
    for name, cfg in PROVIDERS.items():
        cid = getattr(settings, cfg["client_id_setting"], None)
        if cid:
            available.append(name)
    return {"providers": available}


@router.get("/start")
async def start_auth(
    provider: str = Query(..., description="OAuth provider name (e.g. google)"),
    state: str = Query(..., description="Caller-defined state (usually the A2A task ID)"),
    session_id: str = Query("default", description="Session that owns the token"),
):
    """
    Begin the OAuth flow.

    Redirects the user-agent (browser popup) to the provider's consent page.
    After consent the provider redirects back to ``/auth/callback``.
    """
    if provider not in PROVIDERS:
        return HTMLResponse(f"<h3>Unknown provider: {provider}</h3>", status_code=400)

    cfg = PROVIDERS[provider]
    client_id = getattr(settings, cfg["client_id_setting"], None)
    if not client_id:
        return HTMLResponse(
            f"<h3>{provider} OAuth not configured — set {cfg['client_id_setting'].upper()}</h3>",
            status_code=503,
        )

    # CSRF token — binds the callback to this session
    csrf = secrets.token_urlsafe(32)
    _pending_states[csrf] = (session_id, provider)

    params = {
        "client_id": client_id,
        "redirect_uri": f"{settings.auth_redirect_base}/auth/callback",
        "response_type": "code",
        "scope": " ".join(cfg["scopes"]),
        "state": csrf,
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = f"{cfg['authorize_url']}?{urlencode(params)}"

    logger.info("oauth_start", provider=provider, session_id=session_id)
    return RedirectResponse(auth_url)


@router.get("/callback")
async def auth_callback(
    code: str = Query(...),
    state: str = Query(...),
):
    """
    OAuth callback — exchange the authorization code for tokens, store them,
    and return a small HTML page that auto-closes the popup.
    """
    pending = _pending_states.pop(state, None)
    if pending is None:
        return HTMLResponse("<h3>Invalid or expired state parameter.</h3>", status_code=400)

    session_id, provider = pending
    cfg = PROVIDERS[provider]

    client_id = getattr(settings, cfg["client_id_setting"])
    client_secret = getattr(settings, cfg["client_secret_setting"])

    # Exchange code → tokens
    async with aiohttp.ClientSession() as http:
        async with http.post(
            cfg["token_url"],
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": f"{settings.auth_redirect_base}/auth/callback",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            headers={"Accept": "application/json"},
        ) as resp:
            if resp.status != 200:
                body = await resp.text()
                logger.error("oauth_token_exchange_failed", status=resp.status, body=body[:500])
                return HTMLResponse(
                    f"<h3>Token exchange failed ({resp.status})</h3><pre>{body[:500]}</pre>",
                    status_code=502,
                )
            token_data = await resp.json()

    expires_in = token_data.get("expires_in", 3600)
    token = StoredToken(
        provider=provider,
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        expires_at=time.time() + expires_in,
        scopes=token_data.get("scope", "").split(),
    )

    store_token(session_id, provider, token)

    logger.info("oauth_token_stored", provider=provider, session_id=session_id)

    # Return friendly HTML that closes the popup
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html><head><title>Auth Complete</title></head>
        <body style="font-family:system-ui;text-align:center;padding:40px">
            <h2>&#10003; Authentication successful</h2>
            <p>You can close this window. The agent will now scrape with your credentials.</p>
            <script>setTimeout(()=>window.close(), 2000)</script>
        </body></html>
        """,
        status_code=200,
    )


# ── Token store helpers ───────────────────────────────────────────────────────


def store_token(session_id: str, provider: str, token: StoredToken) -> None:
    """Persist a token for a session + provider."""
    if session_id not in _token_store:
        _token_store[session_id] = {}
    _token_store[session_id][provider] = token


def get_token(session_id: str, provider: str) -> StoredToken | None:
    """Retrieve a stored token. Returns ``None`` if not found or expired."""
    bucket = _token_store.get(session_id, {})
    token = bucket.get(provider)
    if token is None:
        return None
    # Treat as expired if within 60 s of expiry
    if token.expires_at and token.expires_at < time.time() + 60:
        logger.info("token_expired", session_id=session_id, provider=provider)
        return None
    return token


def get_auth_headers(session_id: str, provider: str) -> dict[str, str] | None:
    """Return ``Authorization`` header dict if a valid token exists, else ``None``."""
    token = get_token(session_id, provider)
    if token is None:
        return None
    return {"Authorization": f"Bearer {token.access_token}"}


def has_any_token(session_id: str) -> bool:
    """Return ``True`` if the session has at least one stored token."""
    return bool(_token_store.get(session_id))
