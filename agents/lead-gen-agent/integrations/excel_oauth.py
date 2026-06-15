"""
Microsoft Excel / OneDrive OAuth integration.

Uses Microsoft Graph API to read/write Excel workbooks stored in OneDrive.
Auth is via Microsoft Identity Platform (Azure AD OAuth2).

Setup in Azure Portal:
  1. App registrations → New registration
  2. Redirect URI: http://localhost:4567/oauth/excel/callback
  3. API permissions → Microsoft Graph → Delegated:
       Files.ReadWrite, offline_access, User.Read
  4. Copy Application (client) ID and create a client secret
"""
import json
import logging
import os
import time
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)

MS_AUTH_URL  = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
MS_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
SCOPES = "Files.ReadWrite offline_access User.Read"


def _client_id()     -> str | None: return os.getenv("MICROSOFT_CLIENT_ID")
def _client_secret() -> str | None: return os.getenv("MICROSOFT_CLIENT_SECRET")
def _redirect_uri()  -> str:
    return os.getenv("EXCEL_REDIRECT_URI", "http://localhost:4567/oauth/excel/callback")


# ── Auth URL ──────────────────────────────────────────────────────────────────

def get_auth_url(tenant_id: str, workbook_name: str = "Leads", task_id: str | None = None) -> str:
    """Build the Microsoft OAuth consent URL."""
    state = json.dumps({"t": tenant_id, "w": workbook_name, "tid": task_id})
    params = {
        "client_id":     _client_id(),
        "redirect_uri":  _redirect_uri(),
        "response_type": "code",
        "scope":         SCOPES,
        "response_mode": "query",
        "state":         state,
    }
    return f"{MS_AUTH_URL}?{urlencode(params)}"


# ── Token exchange / refresh ──────────────────────────────────────────────────

async def exchange_code(code: str) -> dict:
    """Exchange OAuth code for access_token + refresh_token."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(MS_TOKEN_URL, data={
            "grant_type":    "authorization_code",
            "client_id":     _client_id(),
            "client_secret": _client_secret(),
            "redirect_uri":  _redirect_uri(),
            "scope":         SCOPES,
            "code":          code,
        })
        resp.raise_for_status()
        return resp.json()


async def refresh_access_token(refresh_token: str) -> tuple[str, int]:
    """Refresh an expired access token."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(MS_TOKEN_URL, data={
            "grant_type":    "refresh_token",
            "client_id":     _client_id(),
            "client_secret": _client_secret(),
            "redirect_uri":  _redirect_uri(),
            "scope":         SCOPES,
            "refresh_token": refresh_token,
        })
        resp.raise_for_status()
        data = resp.json()
        expires_at = int(time.time()) + data.get("expires_in", 3600) - 60
        return data["access_token"], expires_at


async def store_tokens(tenant_id: str, token_response: dict, workbook_name: str, store) -> str:
    """Persist tokens + workbook name."""
    expires_at = int(time.time()) + token_response.get("expires_in", 3600) - 60
    await store.set(f"excel_token:{tenant_id}", json.dumps({
        "access_token":  token_response["access_token"],
        "refresh_token": token_response.get("refresh_token", ""),
        "expires_at":    expires_at,
        "workbook_name": workbook_name or "Leads",
    }))
    logger.info("Excel tokens stored for tenant %s (workbook=%s)", tenant_id, workbook_name)
    return workbook_name


async def get_valid_access_token(tenant_id: str, store) -> str | None:
    """Get a valid (non-expired) access token, refreshing if needed."""
    raw = await store.get(f"excel_token:{tenant_id}")
    if not raw:
        return None
    data = json.loads(raw)
    refresh_tok = data.get("refresh_token")
    if not refresh_tok:
        return None
    if time.time() < data.get("expires_at", 0):
        return data["access_token"]
    logger.info("Refreshing Excel access token for tenant %s", tenant_id)
    access_tok, new_expires = await refresh_access_token(refresh_tok)
    data["access_token"] = access_tok
    data["expires_at"]   = new_expires
    await store.set(f"excel_token:{tenant_id}", json.dumps(data))
    return access_tok


async def get_workbook_name(tenant_id: str, store) -> str:
    raw = await store.get(f"excel_token:{tenant_id}")
    if not raw:
        return "Leads"
    return json.loads(raw).get("workbook_name", "Leads")


async def is_connected(tenant_id: str, store) -> bool:
    return bool(await get_valid_access_token(tenant_id, store))


async def delete_tokens(tenant_id: str, store) -> None:
    await store.delete(f"excel_token:{tenant_id}")
