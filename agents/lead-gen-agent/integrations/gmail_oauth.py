"""
Gmail OAuth2 integration.

Flow A — Pre-auth (production):
  GET /oauth/gmail/connect?tenant_id=abc  →  redirect to Google consent
  Google →  GET /oauth/gmail/callback?code=xxx&state=abc  →  store tokens

Flow B — Mid-task interrupt (dev / fallback):
  Agent fires oauth_required interrupt with auth_url
  state param embeds "tenant_id:task_id" so callback auto-resumes the paused task

Sending:
  get_valid_access_token(tenant_id, store) → refreshes if needed
  send_via_gmail_api(access_token, from_email, draft) → Gmail API
"""
import base64
import json
import logging
import os
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL     = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL    = "https://oauth2.googleapis.com/token"
GMAIL_SEND_URL      = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
GMAIL_PROFILE_URL   = "https://gmail.googleapis.com/gmail/v1/users/me/profile"
SCOPES              = " ".join([
    "https://www.googleapis.com/auth/gmail.modify",   # read, label, archive, trash
    "https://www.googleapis.com/auth/gmail.compose",  # create/edit/delete drafts
    "https://www.googleapis.com/auth/gmail.send",     # send messages
])


def _client_id()     -> str | None: return os.getenv("GOOGLE_CLIENT_ID")
def _client_secret() -> str | None: return os.getenv("GOOGLE_CLIENT_SECRET")
def _redirect_uri()  -> str:
    return os.getenv("GMAIL_REDIRECT_URI", "http://localhost:4567/oauth/gmail/callback")


# ── Auth URL ──────────────────────────────────────────────────────────────────

def get_auth_url(tenant_id: str, task_id: str | None = None) -> str:
    """
    Build the Google OAuth consent URL.
    state = "tenant_id" or "tenant_id:task_id" when resuming a paused task.
    """
    state = f"{tenant_id}:{task_id}" if task_id else tenant_id
    params = {
        "client_id":     _client_id(),
        "redirect_uri":  _redirect_uri(),
        "response_type": "code",
        "scope":         SCOPES,
        "access_type":   "offline",   # get refresh_token
        "prompt":        "consent",   # force refresh_token even if already granted
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
        # {access_token, refresh_token, expires_in, token_type, scope}


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
    """
    Get a valid (non-expired) access token for a tenant.
    Reads from store, refreshes if needed, writes back.
    store must implement async get(key)/set(key, value).
    """
    raw = await store.get(f"gmail_token:{tenant_id}")
    if not raw:
        return None

    data = json.loads(raw)
    refresh_tok = data.get("refresh_token")
    if not refresh_tok:
        return None

    expires_at = data.get("expires_at", 0)
    if time.time() < expires_at:
        return data["access_token"]   # still valid

    logger.info("Refreshing Gmail access token for tenant %s", tenant_id)
    access_tok, new_expires = await refresh_access_token(refresh_tok)
    data["access_token"] = access_tok
    data["expires_at"]   = new_expires
    await store.set(f"gmail_token:{tenant_id}", json.dumps(data))
    return access_tok


async def store_tokens(tenant_id: str, token_response: dict, store) -> str:
    """
    Persist tokens from an exchange_code response.
    Returns the sender email address fetched from Gmail profile.
    """
    access_tok = token_response["access_token"]
    expires_at = int(time.time()) + token_response.get("expires_in", 3600) - 60

    # Fetch the sender email from Gmail profile
    sender_email = ""
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                GMAIL_PROFILE_URL,
                headers={"Authorization": f"Bearer {access_tok}"},
            )
            sender_email = r.json().get("emailAddress", "")
    except Exception as e:
        logger.warning("Could not fetch Gmail profile: %s", e)

    await store.set(f"gmail_token:{tenant_id}", json.dumps({
        "access_token":  access_tok,
        "refresh_token": token_response.get("refresh_token", ""),
        "expires_at":    expires_at,
        "email":         sender_email,
    }))
    logger.info("Gmail tokens stored for tenant %s (%s)", tenant_id, sender_email)
    return sender_email


async def get_sender_email(tenant_id: str, store) -> str | None:
    """Return the Gmail address associated with a tenant's stored token."""
    raw = await store.get(f"gmail_token:{tenant_id}")
    if not raw:
        return None
    return json.loads(raw).get("email")


# ── Gmail API send ────────────────────────────────────────────────────────────

async def send_via_gmail_api(access_token: str, from_email: str, draft: dict) -> dict:
    """
    Send a single pre-built draft via the Gmail API.
    draft: {to_email, to_name, subject, body, from_name}
    Returns: {status: sent|failed, email: str, reason: str}
    """
    msg = MIMEMultipart()
    msg["From"]    = f"{draft.get('from_name', 'Sales Team')} <{from_email}>"
    msg["To"]      = draft.get("to_email", "")
    msg["Subject"] = draft.get("subject", "")
    msg.attach(MIMEText(draft.get("body", ""), "plain"))

    raw_b64 = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                GMAIL_SEND_URL,
                headers={"Authorization": f"Bearer {access_token}"},
                json={"raw": raw_b64},
            )
        if resp.status_code in (200, 201):
            logger.info("Gmail API: sent to %s", draft.get("to_email"))
            return {"status": "sent",   "email": draft.get("to_email"), "reason": f"HTTP {resp.status_code}"}
        else:
            logger.warning("Gmail API: %d for %s — %s", resp.status_code, draft.get("to_email"), resp.text[:200])
            return {"status": "failed", "email": draft.get("to_email"), "reason": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as exc:
        logger.error("Gmail API send error for %s: %s", draft.get("to_email"), exc)
        return {"status": "failed", "email": draft.get("to_email"), "reason": str(exc)}


async def send_drafts_via_gmail(access_token: str, from_email: str, drafts: list[dict]) -> dict:
    """Send a batch of drafts via Gmail API. Returns standard email result dict."""
    results = []
    sent = failed = skipped = 0

    for draft in drafts:
        if not draft.get("to_email"):
            skipped += 1
            results.append({"status": "skipped", "email": None, "reason": "no email address"})
            continue
        result = await send_via_gmail_api(access_token, from_email, draft)
        if result["status"] == "sent":
            sent += 1
        else:
            failed += 1
        results.append(result)

    logger.info("send_drafts_via_gmail: sent=%d failed=%d skipped=%d", sent, failed, skipped)
    return {"sent": sent, "failed": failed, "skipped_no_email": skipped, "results": results}
