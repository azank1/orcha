"""
Notion integration — two connection modes:

Mode A (PAT — recommended for teams):
  User creates a Notion integration at notion.so/my-integrations,
  gets an API token, shares their database, and pastes the token here.
  No redirect URI needed.

Mode B (OAuth — for public-facing apps):
  Full OAuth2 flow via Notion's public integration.
  GET /oauth/notion/connect → Notion consent → GET /oauth/notion/callback
"""
import json
import logging
import os
import time
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)

NOTION_AUTH_URL  = "https://api.notion.com/v1/oauth/authorize"
NOTION_TOKEN_URL = "https://api.notion.com/v1/oauth/token"
NOTION_VERSION   = "2022-06-28"


def _client_id()     -> str | None: return os.getenv("NOTION_CLIENT_ID")
def _client_secret() -> str | None: return os.getenv("NOTION_CLIENT_SECRET")
def _redirect_uri()  -> str:
    return os.getenv("NOTION_REDIRECT_URI", "http://localhost:4567/oauth/notion/callback")


# ── Mode A helpers (PAT) ──────────────────────────────────────────────────────

async def store_pat(tenant_id: str, api_token: str, database_id: str, store) -> None:
    """Store a Notion internal integration token + database ID."""
    await store.set(f"notion_token:{tenant_id}", json.dumps({
        "type":        "pat",
        "access_token": api_token,
        "database_id": database_id,
        "stored_at":   int(time.time()),
    }))
    logger.info("Notion PAT stored for tenant %s (db=%s)", tenant_id, database_id)


async def delete_tokens(tenant_id: str, store) -> None:
    await store.delete(f"notion_token:{tenant_id}")


# ── Mode B helpers (OAuth) ────────────────────────────────────────────────────

def get_auth_url(tenant_id: str, database_id: str = "", task_id: str | None = None) -> str:
    """Build the Notion OAuth consent URL."""
    state = json.dumps({"t": tenant_id, "d": database_id, "tid": task_id})
    params = {
        "client_id":     _client_id(),
        "redirect_uri":  _redirect_uri(),
        "response_type": "code",
        "owner":         "user",
        "state":         state,
    }
    return f"{NOTION_AUTH_URL}?{urlencode(params)}"


async def exchange_code(code: str) -> dict:
    """Exchange OAuth code for access token (Notion uses HTTP Basic auth)."""
    import base64
    credentials = base64.b64encode(f"{_client_id()}:{_client_secret()}".encode()).decode()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            NOTION_TOKEN_URL,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type":  "application/json",
                "Notion-Version": NOTION_VERSION,
            },
            json={
                "grant_type":   "authorization_code",
                "code":         code,
                "redirect_uri": _redirect_uri(),
            },
        )
        resp.raise_for_status()
        return resp.json()


async def store_tokens(tenant_id: str, token_response: dict, database_id: str, store) -> str:
    """Persist OAuth tokens + database_id."""
    await store.set(f"notion_token:{tenant_id}", json.dumps({
        "type":          "oauth",
        "access_token":  token_response["access_token"],
        "workspace_id":  token_response.get("workspace_id"),
        "workspace_name": token_response.get("workspace_name"),
        "database_id":   database_id,
        "stored_at":     int(time.time()),
    }))
    logger.info("Notion OAuth tokens stored for tenant %s", tenant_id)
    return database_id


# ── Token access ──────────────────────────────────────────────────────────────

async def get_access_token(tenant_id: str, store) -> str | None:
    """
    Return the stored access token (PAT or OAuth).
    Notion PATs don't expire; OAuth tokens for internal integrations don't either.
    """
    raw = await store.get(f"notion_token:{tenant_id}")
    if not raw:
        return None
    return json.loads(raw).get("access_token")


async def get_database_id(tenant_id: str, store) -> str | None:
    raw = await store.get(f"notion_token:{tenant_id}")
    if not raw:
        return None
    return json.loads(raw).get("database_id")


async def is_connected(tenant_id: str, store) -> bool:
    return bool(await get_access_token(tenant_id, store))


async def get_connection_info(tenant_id: str, store) -> dict:
    raw = await store.get(f"notion_token:{tenant_id}")
    if not raw:
        return {"connected": False}
    data = json.loads(raw)
    return {
        "connected":      True,
        "type":           data.get("type"),
        "database_id":    data.get("database_id"),
        "workspace_name": data.get("workspace_name"),
    }
