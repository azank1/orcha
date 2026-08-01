"""
Google Sheets OAuth2 integration — multi-tenant CRM backend.

Flow:
  GET /oauth/gsheets/connect?tenant_id=abc&spreadsheet_id=1BxiM...
    → redirect to Google consent
  Google → GET /oauth/gsheets/callback?code=xxx&state=abc
    → store tokens + spreadsheet_id

Clients share their Google Sheet with the platform service account OR authorise
via this OAuth flow. The agent then reads/writes leads directly to the sheet.
"""
import json
import logging
import os
import time
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPES = " ".join([
    "https://www.googleapis.com/auth/spreadsheets",   # read + write sheets
    "https://www.googleapis.com/auth/drive.file",     # create/open files the app created
])


def _client_id()     -> str | None: return os.getenv("GOOGLE_CLIENT_ID")
def _client_secret() -> str | None: return os.getenv("GOOGLE_CLIENT_SECRET")
def _redirect_uri()  -> str:
    return os.getenv("GSHEETS_REDIRECT_URI", "http://localhost:4567/oauth/gsheets/callback")


# ── Auth URL ──────────────────────────────────────────────────────────────────

def get_auth_url(tenant_id: str, spreadsheet_id: str = "", task_id: str | None = None) -> str:
    """
    Build the Google OAuth consent URL.
    state encodes tenant_id, spreadsheet_id, and optional task_id as JSON.
    """
    state = json.dumps({"t": tenant_id, "s": spreadsheet_id, "tid": task_id})
    params = {
        "client_id":     _client_id(),
        "redirect_uri":  _redirect_uri(),
        "response_type": "code",
        "scope":         SCOPES,
        "access_type":   "offline",
        "prompt":        "consent",
        "state":         state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


# ── Token exchange / refresh ──────────────────────────────────────────────────

async def exchange_code(code: str) -> dict:
    """Exchange OAuth code for access_token + refresh_token."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(GOOGLE_TOKEN_URL, data={
            "grant_type":    "authorization_code",
            "client_id":     _client_id(),
            "client_secret": _client_secret(),
            "redirect_uri":  _redirect_uri(),
            "code":          code,
        })
        resp.raise_for_status()
        return resp.json()


async def refresh_access_token(refresh_token: str) -> tuple[str, int]:
    """Refresh an expired access token. Returns (access_token, expires_at_unix)."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(GOOGLE_TOKEN_URL, data={
            "grant_type":    "refresh_token",
            "client_id":     _client_id(),
            "client_secret": _client_secret(),
            "refresh_token": refresh_token,
        })
        resp.raise_for_status()
        data = resp.json()
        expires_at = int(time.time()) + data.get("expires_in", 3600) - 60
        return data["access_token"], expires_at


async def get_valid_access_token(tenant_id: str, store) -> str | None:
    """Get a valid (non-expired) access token, refreshing if needed."""
    raw = await store.get(f"gsheets_token:{tenant_id}")
    if not raw:
        return None
    data = json.loads(raw)
    refresh_tok = data.get("refresh_token")
    if not refresh_tok:
        return None
    expires_at = data.get("expires_at", 0)
    if time.time() < expires_at:
        return data["access_token"]
    logger.info("Refreshing Sheets access token for tenant %s", tenant_id)
    access_tok, new_expires = await refresh_access_token(refresh_tok)
    data["access_token"] = access_tok
    data["expires_at"]   = new_expires
    await store.set(f"gsheets_token:{tenant_id}", json.dumps(data))
    return access_tok


async def store_tokens(tenant_id: str, token_response: dict, spreadsheet_id: str, store) -> str:
    """
    Persist tokens + spreadsheet_id.
    Returns the spreadsheet_id for confirmation.
    """
    expires_at = int(time.time()) + token_response.get("expires_in", 3600) - 60
    await store.set(f"gsheets_token:{tenant_id}", json.dumps({
        "access_token":   token_response["access_token"],
        "refresh_token":  token_response.get("refresh_token", ""),
        "expires_at":     expires_at,
        "spreadsheet_id": spreadsheet_id,
    }))
    logger.info("Sheets tokens stored for tenant %s (sheet=%s)", tenant_id, spreadsheet_id)
    return spreadsheet_id


async def get_spreadsheet_id(tenant_id: str, store) -> str | None:
    """Return the Google Sheet ID associated with a tenant's stored token."""
    raw = await store.get(f"gsheets_token:{tenant_id}")
    if not raw:
        return None
    return json.loads(raw).get("spreadsheet_id")


async def update_spreadsheet_id(tenant_id: str, spreadsheet_id: str, store) -> None:
    """Update the stored spreadsheet_id after a sheet is auto-created."""
    raw = await store.get(f"gsheets_token:{tenant_id}")
    if not raw:
        return
    data = json.loads(raw)
    data["spreadsheet_id"] = spreadsheet_id
    await store.set(f"gsheets_token:{tenant_id}", json.dumps(data))
    logger.info("Updated spreadsheet_id for tenant %s: %s", tenant_id, spreadsheet_id)


async def is_connected(tenant_id: str, store) -> bool:
    """Check whether a tenant has a stored Sheets token."""
    return bool(await get_valid_access_token(tenant_id, store))
