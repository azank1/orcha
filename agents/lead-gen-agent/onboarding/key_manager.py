"""
onboarding/key_manager.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Secure credential manager for metaorcha.

Key split:
  Platform keys  (Apollo, Hunter, LLM)  →  .env — clients never see them
  Client keys    (HubSpot PAT)          →  encrypted store, per-tenant
  Client OAuth   (Gmail, Google Sheets) →  token store, per-tenant

CRM routing:
  Each tenant picks one CRM: "hubspot" | "gsheets"
  set_crm_type / get_crm_type controls which backend is used.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import asyncio
import base64
import json
import os
import sqlite3


# ── Encryption ────────────────────────────────────────────────────────────────

def _get_key() -> bytes:
    raw = os.getenv("ENCRYPTION_KEY", "")
    if not raw:
        raise RuntimeError(
            "ENCRYPTION_KEY not set. Generate one with:\n"
            "python -c \"import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())\""
        )
    return base64.urlsafe_b64decode(raw + "==")


def encrypt(value: str) -> str:
    """Simple XOR-based encryption using the ENCRYPTION_KEY. Swap for Fernet in production."""
    try:
        from cryptography.fernet import Fernet
        return Fernet(os.getenv("ENCRYPTION_KEY", "").encode()).encrypt(value.encode()).decode()
    except ImportError:
        # Fallback: base64 obfuscation (install cryptography for real encryption)
        return base64.urlsafe_b64encode(value.encode()).decode()


def decrypt(token: str) -> str:
    try:
        from cryptography.fernet import Fernet
        return Fernet(os.getenv("ENCRYPTION_KEY", "").encode()).decrypt(token.encode()).decode()
    except ImportError:
        return base64.urlsafe_b64decode(token.encode()).decode()
    except Exception:
        # Handle tokens encrypted with base64 fallback
        try:
            return base64.urlsafe_b64decode(token.encode()).decode()
        except Exception:
            return ""


# ── In-memory store (dev/test only — loses all data on restart) ────────────────

class InMemoryStore:
    def __init__(self):
        self._data: dict[str, str] = {}

    async def set(self, key: str, value: str):
        self._data[key] = value

    async def get(self, key: str) -> str | None:
        return self._data.get(key)

    async def delete(self, key: str):
        self._data.pop(key, None)


# ── SQLite store (production — credentials survive restarts) ──────────────────

class SQLiteStore:
    """Persistent key-value store backed by SQLite. Thread-safe via asyncio.to_thread."""

    def __init__(self, db_path: str = "data/credentials.db"):
        self._db_path = db_path
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        con = sqlite3.connect(db_path)
        con.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        con.commit()
        con.close()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path, check_same_thread=False)

    async def set(self, key: str, value: str) -> None:
        def _set():
            con = self._connect()
            con.execute("INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)", (key, value))
            con.commit()
            con.close()
        await asyncio.to_thread(_set)

    async def get(self, key: str) -> str | None:
        def _get():
            con = self._connect()
            row = con.execute("SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
            con.close()
            return row[0] if row else None
        return await asyncio.to_thread(_get)

    async def delete(self, key: str) -> None:
        def _del():
            con = self._connect()
            con.execute("DELETE FROM kv WHERE key = ?", (key,))
            con.commit()
            con.close()
        await asyncio.to_thread(_del)


# ── Key Manager ───────────────────────────────────────────────────────────────

class KeyManager:
    """
    Central credential resolver.
    Combines platform keys (from env) + client keys (from encrypted store).
    """

    def __init__(self, store=None):
        self.store = store or InMemoryStore()

    # ── Generic PAT storage ───────────────────────────────────────────────────

    async def store_user_key(self, tenant_id: str, service: str, token: str):
        """Store a client's token encrypted. service: 'hubspot' | 'sendgrid'"""
        await self.store.set(f"{tenant_id}:{service}", encrypt(token))

    async def get_user_key(self, tenant_id: str, service: str) -> str | None:
        """Retrieve and decrypt a client's stored token."""
        raw = await self.store.get(f"{tenant_id}:{service}")
        if not raw:
            return None
        try:
            return decrypt(raw)
        except Exception:
            return None

    async def delete_user_key(self, tenant_id: str, service: str):
        await self.store.delete(f"{tenant_id}:{service}")

    # ── HubSpot PAT ───────────────────────────────────────────────────────────

    async def store_hubspot_token(self, tenant_id: str, token: str):
        """Store client's HubSpot Private App Token."""
        await self.store_user_key(tenant_id, "hubspot", token)
        await self.set_crm_type(tenant_id, "hubspot")

    async def get_hubspot_token(self, tenant_id: str) -> str | None:
        return await self.get_user_key(tenant_id, "hubspot")

    async def delete_hubspot_token(self, tenant_id: str):
        await self.delete_user_key(tenant_id, "hubspot")
        crm = await self.get_crm_type(tenant_id)
        if crm == "hubspot":
            await self.store.delete(f"{tenant_id}:crm_type")

    # ── Notion PAT ───────────────────────────────────────────────────────────

    async def store_notion_token(self, tenant_id: str, api_token: str, database_id: str):
        """Store a Notion internal integration token + database ID."""
        from integrations.notion_oauth import store_pat
        await store_pat(tenant_id, api_token, database_id, self.store)
        await self.set_crm_type(tenant_id, "notion")

    async def get_notion_database_id(self, tenant_id: str) -> str | None:
        from integrations.notion_oauth import get_database_id
        return await get_database_id(tenant_id, self.store)

    async def delete_notion_token(self, tenant_id: str):
        from integrations.notion_oauth import delete_tokens
        await delete_tokens(tenant_id, self.store)
        if await self.get_crm_type(tenant_id) == "notion":
            await self.store.delete(f"{tenant_id}:crm_type")

    # ── CRM type routing ──────────────────────────────────────────────────────

    async def set_crm_type(self, tenant_id: str, crm_type: str):
        """Set which CRM backend this tenant uses: 'hubspot' | 'gsheets'"""
        await self.store.set(f"{tenant_id}:crm_type", crm_type)

    async def get_crm_type(self, tenant_id: str) -> str | None:
        """Returns 'hubspot' | 'gsheets' | None (not connected)."""
        return await self.store.get(f"{tenant_id}:crm_type")

    # ── Google Sheets config ──────────────────────────────────────────────────

    async def get_gsheets_spreadsheet_id(self, tenant_id: str) -> str | None:
        """Return the Google Sheets spreadsheet ID for a tenant."""
        from integrations.gsheets_oauth import get_spreadsheet_id
        return await get_spreadsheet_id(tenant_id, self.store)

    # ── Resolve full credential set for a request ─────────────────────────────

    async def resolve(self, tenant_id: str) -> dict:
        """
        Build the full credentials dict for a tenant's lead gen request.
        Platform keys come from env; client keys from encrypted store.
        """
        hubspot_key = await self.get_hubspot_token(tenant_id)
        provider    = os.getenv("LLM_PROVIDER", "openrouter").lower()

        return {
            # LLM key
            "anthropic_api_key":  os.getenv("ANTHROPIC_API_KEY")  if provider == "anthropic"  else None,
            "openai_api_key":     os.getenv("OPENAI_API_KEY")     if provider == "openai"     else None,
            "grok_api_key":       os.getenv("GROK_API_KEY")       if provider == "grok"       else None,
            "openrouter_api_key": os.getenv("OPENROUTER_API_KEY") if provider == "openrouter" else None,

            # Data APIs — platform pays
            "apollo_api_key": os.getenv("APOLLO_API_KEY") or None,
            "hunter_api_key": os.getenv("HUNTER_API_KEY") or None,

            # Client's CRM token (HubSpot PAT)
            "hubspot_api_key": hubspot_key or None,
        }

    # ── Connected service listing ─────────────────────────────────────────────

    async def list_connected_services(self, tenant_id: str) -> list[str]:
        """Returns which services this tenant has connected."""
        connected = []
        for svc in ["hubspot", "sendgrid"]:
            if await self.get_user_key(tenant_id, svc):
                connected.append(svc)

        # Check Gmail
        gmail_raw = await self.store.get(f"gmail_token:{tenant_id}")
        if gmail_raw:
            connected.append("gmail")

        # Check Google Sheets
        gsheets_raw = await self.store.get(f"gsheets_token:{tenant_id}")
        if gsheets_raw:
            connected.append("gsheets")

        return connected

    async def has_crm_connected(self, tenant_id: str) -> tuple[bool, str | None]:
        """Returns (connected: bool, crm_type: str | None)."""
        crm_type = await self.get_crm_type(tenant_id)
        if crm_type == "hubspot":
            token = await self.get_hubspot_token(tenant_id)
            return bool(token), "hubspot" if token else None
        if crm_type == "gsheets":
            from integrations.gsheets_oauth import get_valid_access_token
            token = await get_valid_access_token(tenant_id, self.store)
            return bool(token), "gsheets" if token else None
        if crm_type == "notion":
            from integrations.notion_oauth import get_access_token
            token = await get_access_token(tenant_id, self.store)
            return bool(token), "notion" if token else None
        if crm_type == "excel":
            from integrations.excel_oauth import get_valid_access_token
            token = await get_valid_access_token(tenant_id, self.store)
            return bool(token), "excel" if token else None
        return False, None

    async def get_crm_credentials(self, tenant_id: str) -> dict:
        """Return all CRM-related credentials for agent.run()."""
        crm_type = await self.get_crm_type(tenant_id)
        base = {"crm_type": crm_type}
        if crm_type == "gsheets":
            from integrations.gsheets_oauth import get_spreadsheet_id
            base["spreadsheet_id"] = await get_spreadsheet_id(tenant_id, self.store)
        elif crm_type == "notion":
            from integrations.notion_oauth import get_database_id
            base["notion_database_id"] = await get_database_id(tenant_id, self.store)
        elif crm_type == "excel":
            from integrations.excel_oauth import get_workbook_name
            base["excel_workbook_name"] = await get_workbook_name(tenant_id, self.store)
        return base

    async def has_required_keys(self, tenant_id: str) -> tuple[bool, list[str]]:
        """Check if a tenant has everything needed. Returns (ready: bool, missing: list[str])"""
        from core.llm_provider import get_api_key_name
        missing = []
        if not os.getenv(get_api_key_name()):
            missing.append(f"{get_api_key_name()} (platform — set in .env)")
        connected, _ = await self.has_crm_connected(tenant_id)
        if not connected:
            missing.append("CRM (connect HubSpot or Google Sheets via /crm/hubspot/connect or /oauth/gsheets/connect)")
        return len(missing) == 0, missing


# ── FastAPI settings routes ───────────────────────────────────────────────────

def register_settings_routes(app, key_manager: KeyManager):
    """Register credential management routes on the FastAPI app."""
    from fastapi import Request, HTTPException
    from pydantic import BaseModel

    class KeySubmission(BaseModel):
        token: str

    @app.post("/settings/keys/{service}")
    async def save_key(service: str, body: KeySubmission, request: Request):
        tenant_id = getattr(request.state, "user_id", "default")
        if service not in ["hubspot", "sendgrid"]:
            raise HTTPException(400, f"Unknown service. Allowed: hubspot, sendgrid")
        if len(body.token) < 10:
            raise HTTPException(400, "Token too short")
        await key_manager.store_user_key(tenant_id, service, body.token)
        return {"status": "connected", "service": service}

    @app.delete("/settings/keys/{service}")
    async def delete_key(service: str, request: Request):
        tenant_id = getattr(request.state, "user_id", "default")
        await key_manager.delete_user_key(tenant_id, service)
        return {"status": "disconnected", "service": service}

    @app.get("/settings/keys")
    async def list_keys(request: Request):
        tenant_id = getattr(request.state, "user_id", "default")
        connected = await key_manager.list_connected_services(tenant_id)
        crm_type  = await key_manager.get_crm_type(tenant_id)
        return {
            "connected":        connected,
            "crm_type":         crm_type,
            "platform_managed": ["apollo", "hunter"],
        }
