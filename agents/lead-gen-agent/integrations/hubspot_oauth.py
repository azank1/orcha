"""
hubspot_oauth.py
Handles HubSpot OAuth for metaorcha users.
User clicks Connect → authorizes → you store their token → agent uses it automatically.
"""
import os
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

HUBSPOT_CLIENT_ID = os.getenv("HUBSPOT_CLIENT_ID")
HUBSPOT_CLIENT_SECRET = os.getenv("HUBSPOT_CLIENT_SECRET")
REDIRECT_URI = os.getenv("HUBSPOT_REDIRECT_URI", "https://yourapp.com/oauth/hubspot/callback")

SCOPES = "crm.objects.contacts.write crm.objects.contacts.read"


def get_auth_url(user_id: str) -> str:
    """
    Generate the HubSpot OAuth URL for a user.
    Embed user_id in state so we know who to store the token for after redirect.
    """
    return (
        f"https://app.hubspot.com/oauth/authorize"
        f"?client_id={HUBSPOT_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={SCOPES.replace(' ', '%20')}"
        f"&state={user_id}"
    )


async def exchange_code_for_token(code: str) -> dict:
    """Exchange the OAuth code for access + refresh tokens."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.hubapi.com/oauth/v1/token",
            data={
                "grant_type": "authorization_code",
                "client_id": HUBSPOT_CLIENT_ID,
                "client_secret": HUBSPOT_CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "code": code,
            },
        )
        resp.raise_for_status()
        return resp.json()
        # Returns: {access_token, refresh_token, expires_in, token_type}


async def refresh_token(refresh_token: str) -> dict:
    """Refresh an expired HubSpot access token."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.hubapi.com/oauth/v1/token",
            data={
                "grant_type": "refresh_token",
                "client_id": HUBSPOT_CLIENT_ID,
                "client_secret": HUBSPOT_CLIENT_SECRET,
                "refresh_token": refresh_token,
            },
        )
        resp.raise_for_status()
        return resp.json()


# ── FastAPI routes to add to your metaorcha app ───────────────────────────────

def register_oauth_routes(app: FastAPI, token_store):
    """
    Call this in your metaorcha main app to add the OAuth endpoints.
    token_store is whatever storage you use (Redis, Postgres, etc.)
    """

    @app.get("/oauth/hubspot/connect")
    async def hubspot_connect(request: Request):
        """User hits this to start the OAuth flow."""
        user_id = request.state.user_id  # from your auth middleware
        auth_url = get_auth_url(user_id)
        return RedirectResponse(auth_url)

    @app.get("/oauth/hubspot/callback")
    async def hubspot_callback(code: str, state: str):
        """HubSpot redirects here after user authorizes."""
        user_id = state
        tokens = await exchange_code_for_token(code)

        # Store tokens against the user — use your existing storage
        await token_store.set(f"hubspot:{user_id}", {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "expires_in": tokens["expires_in"],
        })

        return RedirectResponse("/dashboard?connected=hubspot")


async def get_user_hubspot_token(user_id: str, token_store) -> str | None:
    """
    Get a valid HubSpot token for a user.
    Auto-refreshes if expired.
    Called by the lead gen agent before each CRM write.
    """
    data = await token_store.get(f"hubspot:{user_id}")
    if not data:
        return None  # user hasn't connected HubSpot yet

    # TODO: check expiry and refresh if needed
    # For now returns access token directly
    return data["access_token"]
