"""Shopify OAuth routes for agent-managed A2A OAuth flow."""

from __future__ import annotations

import secrets
import urllib.parse

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from .config import settings
from .token_store import put_token

router = APIRouter(prefix="/auth", tags=["auth"])


def _parse_state(state: str) -> tuple[str | None, str | None]:
    # Expected format from SuperAgent: "<session_id>:<agent_id>:<nonce>"
    parts = state.split(":")
    if len(parts) < 3:
        return None, None
    session_id = parts[0]
    agent_id = ":".join(parts[1:-1])
    if not session_id or not agent_id:
        return None, None
    return session_id, agent_id


def _normalise_shop_base(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    if not s.startswith(("http://", "https://")):
        s = f"https://{s}"
    return s.rstrip("/")


@router.get("/start")
async def oauth_start(
    client_id: str = Query(default=""),
    response_type: str = Query(default="code"),
    scope: str = Query(default=""),
    state: str = Query(default_factory=lambda: secrets.token_urlsafe(8)),
    redirect_uri: str = Query(default=""),
    shop: str = Query(default=""),
) -> RedirectResponse:
    """
    Bridge route used as emerge.yaml authorization_url.

    SuperAgent builds the URL against this endpoint. This endpoint then redirects
    to the real Shopify authorize endpoint for the configured store.
    """
    cid = client_id or settings.shopify_oauth_client_id or ""
    ruri = redirect_uri or settings.shopify_oauth_redirect_uri
    if not cid:
        raise HTTPException(status_code=503, detail="SHOPIFY_OAUTH_CLIENT_ID is not configured")
    if response_type.lower() != "code":
        raise HTTPException(status_code=400, detail="Unsupported response_type")

    shop_base = _normalise_shop_base(shop) or _normalise_shop_base(settings.shopify_store_url or "")
    if not shop_base:
        raise HTTPException(status_code=503, detail="SHOPIFY_STORE_URL is not configured")

    query = urllib.parse.urlencode(
        {
            "client_id": cid,
            "scope": scope or settings.shopify_oauth_scopes,
            "redirect_uri": ruri,
            "state": state,
        }
    )
    target = f"{shop_base}/admin/oauth/authorize?{query}"
    return RedirectResponse(url=target, status_code=302)


@router.get("/callback")
async def oauth_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    shop: str | None = Query(default=None),
    error: str | None = Query(default=None),
) -> dict[str, str]:
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")
    if not settings.shopify_oauth_client_id or not settings.shopify_oauth_client_secret:
        raise HTTPException(status_code=503, detail="Shopify OAuth client is not configured")

    shop_base = _normalise_shop_base(shop or "") or _normalise_shop_base(settings.shopify_store_url or "")
    if not shop_base:
        raise HTTPException(status_code=503, detail="Shopify store URL is not configured")

    token_url = f"{shop_base}/admin/oauth/access_token"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            token_url,
            json={
                "client_id": settings.shopify_oauth_client_id,
                "client_secret": settings.shopify_oauth_client_secret,
                "code": code,
            },
        )
    if resp.status_code >= 300:
        raise HTTPException(status_code=400, detail="Token exchange failed")

    data = resp.json()
    access = data.get("access_token")
    if not access:
        raise HTTPException(status_code=400, detail="No access_token in token response")

    session_id, agent_id = _parse_state(state)
    if not session_id or not agent_id:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    put_token(session_id, access_token=access)

    resume_url = f"{settings.gateway_base_url.rstrip('/')}/auth/sessions/{session_id}/resume-agent-oauth"
    async with httpx.AsyncClient(timeout=20.0) as client:
        resume_resp = await client.post(
            resume_url,
            json={"agent_id": agent_id, "status": "ok"},
        )
    if resume_resp.status_code >= 300:
        raise HTTPException(status_code=502, detail="Token stored, but failed to resume session")

    return {"status": "ok", "message": "Shopify access granted and session resumed"}
