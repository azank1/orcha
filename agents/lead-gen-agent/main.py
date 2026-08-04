"""
Lead Gen Agent — A2A Server
FastAPI app exposing the agent as a discoverable A2A endpoint.

Endpoints:
  POST /                        — A2A JSON-RPC (message/send + tasks/get)
  POST /run                     — Standalone run (no A2A protocol needed)
  GET  /.well-known/agent.json  — A2A discovery
  GET  /.well-known/agent-card  — Legacy discovery (backwards compat)
  GET  /health                  — Health check

  OAuth:
    GET  /oauth/gmail/connect       — Start Gmail OAuth
    GET  /oauth/gmail/callback      — Google redirects here after Gmail consent
    GET  /oauth/gsheets/connect     — Start Google Sheets OAuth
    GET  /oauth/gsheets/callback    — Google redirects here after Sheets consent
    GET  /oauth/notion/connect      — Start Notion OAuth (public integration)
    GET  /oauth/notion/callback     — Notion redirects here after consent
    GET  /oauth/excel/connect       — Start Microsoft Excel OAuth
    GET  /oauth/excel/callback      — Microsoft redirects here after consent

  CRM management:
    POST   /crm/hubspot/connect     — Save HubSpot Private App Token
    DELETE /crm/hubspot/disconnect  — Remove HubSpot token
    POST   /crm/notion/connect      — Save Notion PAT + database_id (internal integration)
    POST   /crm/select              — Switch active CRM type for a tenant
    GET    /crm/status              — Current CRM type + connection status

Interrupt support:
  Tasks can enter "input-required" status mid-execution for:
  • Email draft review (HITL_APPROVAL)    — user edits/approves outreach emails before sending
  • HubSpot auth (AGENT_CLARIFICATION)   — user provides their HubSpot Private App Token
  • Gmail OAuth  (OAUTH_REQUIRED)        — agent pauses and returns auth_url; callback auto-resumes
  • Sheets OAuth (OAUTH_REQUIRED)        — same pattern as Gmail
  Resume via message/send with the original taskId in message.taskId.
"""
import asyncio
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("lead_gen_agent")

from core.agent import LeadGenAgent
from core.context import set_credentials, api_keys
from onboarding.key_manager import KeyManager, SQLiteStore
from integrations.gmail_oauth import (
    get_auth_url as gmail_auth_url,
    exchange_code as gmail_exchange_code,
    store_tokens as gmail_store_tokens,
    get_valid_access_token,
    get_sender_email,
    send_drafts_via_gmail,
)
from integrations.gsheets_oauth import (
    get_auth_url as gsheets_auth_url,
    exchange_code as gsheets_exchange_code,
    store_tokens as gsheets_store_tokens,
    get_valid_access_token as gsheets_get_token,
    get_spreadsheet_id,
    is_connected as gsheets_is_connected,
)
from integrations.notion_oauth import (
    get_auth_url as notion_auth_url,
    exchange_code as notion_exchange_code,
    store_pat as notion_store_pat,
    get_access_token as notion_get_token,
    get_database_id as notion_get_db_id,
    is_connected as notion_is_connected,
    delete_tokens as notion_delete_tokens,
)
from integrations.excel_oauth import (
    get_auth_url as excel_auth_url,
    exchange_code as excel_exchange_code,
    store_tokens as excel_store_tokens,
    get_valid_access_token as excel_get_token,
    get_workbook_name as excel_get_workbook_name,
    is_connected as excel_is_connected,
    delete_tokens as excel_delete_tokens,
)

limiter = Limiter(key_func=get_remote_address)

agent: LeadGenAgent | None = None
key_manager: KeyManager = KeyManager(store=SQLiteStore("data/credentials.db"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent
    logger.info("Starting Lead Gen Agent server...")
    agent = LeadGenAgent()
    logger.info("Agent initialized. Server ready.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Lead Gen Agent",
    description="A2A-compatible B2B lead generation agent. Supports HubSpot and Google Sheets CRM.",
    version="1.2.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)


# ── In-memory A2A task store ──────────────────────────────────────────────────

@dataclass
class A2ATask:
    id: str
    # submitted | working | input-required | completed | failed
    status: str
    artifacts: list = field(default_factory=list)
    message: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    # Interrupt support: task pauses here, resumes when caller sends taskId
    pause_event: asyncio.Event = field(default_factory=asyncio.Event)
    resume_data: dict | None = None
    interrupt_meta: dict | None = None  # surfaced in tasks/get when input-required


_a2a_tasks: dict[str, A2ATask] = {}


class ToolSettingsRequest(BaseModel):
    tenant_id: str = "default"
    tool: str
    action: str
    config: dict[str, Any] = Field(default_factory=dict)


SUPPORTED_CRM_OPTIONS: tuple[str, ...] = ("hubspot", "gsheets", "notion", "excel")


# ── Auth ──────────────────────────────────────────────────────────────────────

def verify_api_key(request: Request):
    """Validate X-API-Key header. Skip if AGENT_API_KEY not configured (dev mode)."""
    expected_key = os.getenv("AGENT_API_KEY")
    if not expected_key:
        logger.warning("AGENT_API_KEY not set — running in unauthenticated dev mode")
        return
    provided_key = request.headers.get("X-API-Key")
    if not provided_key or provided_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header")



# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_agent_card() -> dict:
    card_path = Path(__file__).parent / "agent_card.json"
    card = json.loads(card_path.read_text()) if card_path.exists() else {"name": "lead-gen-agent", "version": "1.1.0"}
    base_url = os.getenv("AGENT_BASE_URL", "http://localhost:4567").rstrip("/")
    card["url"] = base_url
    return card


def _format_run_result(result: dict) -> str:
    lines = [
        f"Lead Gen Agent completed — status: {result.get('status', 'success')}",
        f"  Leads found:        {result.get('leads_found', 0)}",
        f"  Leads qualified:    {result.get('leads_qualified', 0)}",
        f"  Written to CRM:     {result.get('leads_written_to_crm', 0)}",
        f"  Emails sent:        {result.get('emails_sent', 0)}",
    ]
    if result.get("summary"):
        lines.append(f"\nSummary: {result['summary']}")
    qualified = result.get("qualified_leads", [])
    if qualified:
        lines.append(f"\nTop {min(5, len(qualified))} qualified leads:")
        for lead in qualified[:5]:
            name    = lead.get("full_name", "Unknown")
            title   = lead.get("title", "")
            company = lead.get("company", "")
            score   = lead.get("icp_score", "?")
            email   = lead.get("email") or "no email"
            lines.append(f"  • {name} — {title} at {company} (score: {score}, {email})")
        if len(qualified) > 5:
            lines.append(f"  … and {len(qualified) - 5} more")
    return "\n".join(lines)


def _parse_resume_data(parts: list[dict]) -> dict:
    """
    Extract resume payload from message parts.
    Tries JSON for text parts (to handle approved+drafts), then falls back to {"text": value}.
    Data parts are merged directly.
    """
    resume: dict = {}
    for part in parts:
        kind = part.get("kind")
        if kind == "text":
            text = part.get("text", "")
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    resume.update(parsed)
                    continue
            except (json.JSONDecodeError, ValueError):
                pass
            resume["text"] = text
        elif kind == "data":
            data = part.get("data", {})
            if isinstance(data, dict):
                resume.update(data)
    return resume


# ── Interrupt callbacks (wired per-task into the agent) ──────────────────────

def _make_review_callback(task_id: str):
    """
    Returns an async callback that pauses the agent task so the user can
    review and optionally edit the outreach email drafts before sending.

    Interrupt type: HITL_APPROVAL
    Resume value shapes:
      • approve (no edits):  "approve"  or  {"approved": true}
      • approve with edits:  {"approved": true, "edited_drafts": [...]}
      • deny / cancel:       "deny"     or  {"approved": false}
    """
    async def review_callback(drafts: list[dict]) -> list[dict]:
        task = _a2a_tasks[task_id]
        n = len(drafts)
        task.interrupt_meta = {
            # hint for a2a_handler._classify_input_required
            "interrupt_type": "approval",
            "action_description": (
                f"Review {n} outreach email draft{'s' if n != 1 else ''} before sending. "
                "You can edit subject / body for each draft."
            ),
            "risk_level": "medium",
            "agent_display_name": "Lead Gen Agent",
            "capability_name": "send_outreach_emails",
            "drafts": drafts,
            "resume_schema": {
                "approved": "bool (required)",
                "edited_drafts": "optional list of edited draft objects",
                "action": "optional string: approve | deny | draft_only",
            },
        }
        task.message = (
            f"Please review and approve the {n} outreach email draft"
            f"{'s' if n != 1 else ''} before sending."
        )
        task.status = "input-required"
        logger.info("Task %s → input-required (email review, %d draft(s))", task_id, n)

        # Wait for resume from _handle_message_send
        await task.pause_event.wait()
        task.pause_event.clear()
        task.status = "working"

        resume = task.resume_data or {}
        text   = resume.get("text", "").strip().lower()

        # Detect denial / draft-only intent
        approved_flag = resume.get("approved")
        action = str(resume.get("action", "")).strip().lower()
        if text == "deny" or approved_flag is False or action in {"deny", "draft_only"}:
            logger.info("Task %s: user requested no send after email review", task_id)
            return []

        # Return edited drafts if user provided them, otherwise send originals
        edited = resume.get("edited_drafts")
        if edited and isinstance(edited, list):
            logger.info("Task %s: user provided %d edited draft(s)", task_id, len(edited))
            return edited
        return drafts

    return review_callback


def _make_gmail_oauth_callback(task_id: str, tenant_id: str):
    """
    Returns an async callback that pauses the agent when no Gmail token is found.

    Interrupt type: OAUTH_REQUIRED
    The auth_url embeds task_id in the OAuth state param so the /oauth/gmail/callback
    route can auto-resume this task — the super-agent only needs to poll, no manual
    resume message required.
    """
    async def gmail_oauth_callback() -> tuple[str, str]:
        """Returns (access_token, sender_email) after OAuth completes."""
        task = _a2a_tasks[task_id]
        auth_url = gmail_auth_url(tenant_id, task_id)

        task.interrupt_meta = {
            "interrupt_type":    "oauth_required",
            "provider":          "gmail",
            "auth_url":          auth_url,
            "instructions":      (
                "Visit the auth_url to connect Gmail. "
                "After authorising, the agent resumes automatically — no further action needed."
            ),
            "agent_display_name": "Lead Gen Agent",
            "tenant_id":          tenant_id,
        }
        task.message = "Gmail authorisation required. Visit auth_url to connect and the agent will resume automatically."
        task.status  = "input-required"
        logger.info("Task %s → input-required (Gmail OAuth for tenant %s)", task_id, tenant_id)

        # Wait — the /oauth/gmail/callback route will set this event
        await task.pause_event.wait()
        task.pause_event.clear()
        task.status = "working"

        # Retrieve the freshly stored token
        access_token  = await get_valid_access_token(tenant_id, key_manager.store)
        sender_email  = await get_sender_email(tenant_id, key_manager.store) or ""
        if not access_token:
            raise ValueError("Gmail OAuth completed but token not found in store.")
        logger.info("Task %s: Gmail OAuth complete, sender=%s", task_id, sender_email)
        return access_token, sender_email

    return gmail_oauth_callback


def _make_hubspot_auth_callback(task_id: str, tenant_id: str):
    """
    Returns a callback that:
    1. Checks the key_manager store first (token persisted from a previous run)
    2. If not found, pauses the task and asks the user to paste their HubSpot PAT
    3. On first paste, stores the token so future runs skip the interrupt

    Interrupt type: AGENT_CLARIFICATION
    """
    async def hubspot_auth_callback() -> str:
        # ── Check persistent store first ──────────────────────────────────────
        stored = await key_manager.get_hubspot_token(tenant_id)
        if stored:
            logger.info("Task %s: HubSpot token loaded from store for tenant %s", task_id, tenant_id)
            return stored

        # ── Not stored — ask user via HITL interrupt ──────────────────────────
        task = _a2a_tasks[task_id]
        task.interrupt_meta = {
            "interrupt_type": "clarification",
            "question": (
                "HubSpot Private App Token required.\n\n"
                "To create one:\n"
                "1. HubSpot → Settings → Integrations → Private Apps\n"
                "2. Create a private app\n"
                "3. Scopes: crm.objects.contacts.write, crm.objects.contacts.read, crm.objects.deals.write, crm.objects.deals.read\n"
                "4. Copy the token and paste it here.\n\n"
                "Your token will be saved — you won't be asked again."
            ),
            "agent_display_name": "Lead Gen Agent",
            "agent_id": "lead-gen",
        }
        task.message = "HubSpot Private App Token required to write leads to CRM."
        task.status = "input-required"
        logger.info("Task %s → input-required (HubSpot auth, tenant=%s)", task_id, tenant_id)

        await task.pause_event.wait()
        task.pause_event.clear()
        task.status = "working"

        resume = task.resume_data or {}
        token = (
            resume.get("response") or resume.get("answer") or resume.get("text") or ""
        ).strip()

        if not token:
            raise ValueError("HubSpot token not provided — CRM write skipped.")

        # Persist so future tasks don't need to ask again
        await key_manager.store_hubspot_token(tenant_id, token)
        logger.info("Task %s: HubSpot token received and stored for tenant %s", task_id, tenant_id)
        return token

    return hubspot_auth_callback


def _make_crm_setup_callback(task_id: str, tenant_id: str):
    """
    Returns a callback that pauses the agent so the user can select and connect
    a CRM. Works with or without a custom UI:
      - UI path: frontend handles CRM setup, then resumes task.
      - API path: caller resumes with crm_type (+ optional hubspot_token).

    Interrupt type: crm_setup → mapped to InterruptType.CRM_SETUP by a2a_handler

    IMPORTANT: Never return a CRM kind (e.g. gsheets) unless that CRM is actually
    connected for the tenant. Returning "gsheets" without OAuth caused CRM writes
    to fail while Gmail outreach still succeeded — a silent split behaviour.
    """
    async def crm_setup_callback() -> str:
        """Returns the crm_type string ('gsheets', 'hubspot', etc.) after setup."""
        supported = frozenset(SUPPORTED_CRM_OPTIONS)
        base_url = os.getenv("AGENT_BASE_URL", "http://localhost:4567").rstrip("/")

        while True:
            crm_type = await key_manager.get_crm_type(tenant_id)
            if crm_type:
                connected, detail = await key_manager.has_crm_connected(tenant_id)
                if connected:
                    logger.info(
                        "Task %s: CRM ready (%s) — skipping setup",
                        task_id,
                        crm_type,
                    )
                    return crm_type
                logger.info(
                    "Task %s: CRM %s configured but not connected (%s) — prompting setup",
                    task_id,
                    crm_type,
                    detail,
                )

            task = _a2a_tasks[task_id]
            task.interrupt_meta = {
                "interrupt_type":     "crm_setup",
                "tenant_id":          tenant_id,
                "agent_display_name": "Lead Gen Agent",
                "lead_gen_url":       base_url,
                "options": list(SUPPORTED_CRM_OPTIONS),
                "resume_schema": {
                    "crm_type": "required one of: hubspot|gsheets|notion|excel",
                    "hubspot_token": "optional string (only for hubspot PAT flow)",
                },
                "connection_urls": {
                    "hubspot_pat": f"{base_url}/crm/hubspot/connect",
                    "gsheets_oauth": f"{base_url}/oauth/gsheets/connect?tenant_id={tenant_id}&task_id={task_id}",
                    "notion_oauth": f"{base_url}/oauth/notion/connect?tenant_id={tenant_id}&task_id={task_id}",
                    "excel_oauth": f"{base_url}/oauth/excel/connect?tenant_id={tenant_id}&task_id={task_id}",
                },
            }
            task.message = (
                "Connect a CRM to save your qualified leads. "
                "Pick HubSpot, Google Sheets, Excel, or Notion, complete OAuth (or HubSpot PAT), "
                "then continue."
            )
            task.status = "input-required"
            logger.info("Task %s → input-required (CRM setup, tenant=%s)", task_id, tenant_id)

            await task.pause_event.wait()
            task.pause_event.clear()
            task.status = "working"

            resume = task.resume_data or {}
            requested_crm = str(resume.get("crm_type", "")).strip().lower()
            hubspot_token = str(
                resume.get("hubspot_token")
                or resume.get("token")
                or ""
            ).strip()

            if requested_crm in supported:
                if requested_crm == "hubspot" and hubspot_token:
                    await key_manager.store_hubspot_token(tenant_id, hubspot_token)
                else:
                    await key_manager.set_crm_type(tenant_id, requested_crm)

            # Loop until get_crm_type + has_crm_connected both succeed

    return crm_setup_callback


# ── A2A background task executor ─────────────────────────────────────────────

async def _run_agent_task(task_id: str, query: str, opts: dict) -> None:
    """Execute the agent in the background and update the task store."""
    task = _a2a_tasks[task_id]
    task.status = "working"

    creds_dict: dict = opts.get("credentials") or {}
    tenant_id: str   = opts.get("tenant_id") or creds_dict.get("tenant_id") or "default"
    ctx_token = None
    if creds_dict:
        ctx_token = set_credentials({k.upper(): v for k, v in creds_dict.items() if v})

    # Design C: super-agent injected a Gmail refresh token directly
    if creds_dict.get("gmail_refresh_token"):
        from integrations.gmail_oauth import refresh_access_token, store_tokens as _store
        try:
            token_data = {
                "access_token": "", "refresh_token": creds_dict["gmail_refresh_token"],
                "expires_in": 0,
            }
            await gmail_store_tokens(tenant_id, token_data, key_manager.store)
        except Exception as e:
            logger.warning("Could not store injected Gmail token: %s", e)

    try:
        # Optional structured preference from orchestrator / gateway (A2A data part)
        _pref_crm = str(opts.get("crm_type") or "").strip().lower()
        if _pref_crm in SUPPORTED_CRM_OPTIONS:
            await key_manager.set_crm_type(tenant_id, _pref_crm)

        # Resolve full CRM credentials for this tenant
        crm_creds = await key_manager.get_crm_credentials(tenant_id)
        crm_type  = crm_creds.get("crm_type")

        result = await agent.run(
            query=query,
            max_leads=int(opts.get("max_leads", 20)),
            write_to_crm=bool(opts.get("write_to_crm", True)),
            send_outreach_email=bool(opts.get("send_outreach_email", True)),
            review_callback=_make_review_callback(task_id),
            hubspot_auth_callback=_make_hubspot_auth_callback(task_id, tenant_id),
            gmail_oauth_callback=_make_gmail_oauth_callback(task_id, tenant_id),
            crm_setup_callback=_make_crm_setup_callback(task_id, tenant_id),
            tenant_id=tenant_id,
            gmail_token_store=key_manager.store,
            crm_type=crm_type,
            gsheets_token_store=key_manager.store,
            spreadsheet_id=crm_creds.get("spreadsheet_id"),
            notion_token_store=key_manager.store,
            notion_database_id=crm_creds.get("notion_database_id"),
            excel_token_store=key_manager.store,
            excel_workbook_name=crm_creds.get("excel_workbook_name", "Leads"),
        )

        task.artifacts = [
            {
                "parts": [
                    {"kind": "text", "text": _format_run_result(result)},
                    {"kind": "data", "data": result},
                ]
            }
        ]
        task.status = "completed"
        task.interrupt_meta = None
        logger.info(
            "A2A task %s completed — found=%d qualified=%d",
            task_id,
            result.get("leads_found", 0),
            result.get("leads_qualified", 0),
        )
    except Exception as exc:
        logger.error("A2A task %s failed: %s", task_id, exc, exc_info=True)
        task.status = "failed"
        task.message = str(exc)
        task.interrupt_meta = None
    finally:
        if ctx_token is not None:
            api_keys.reset(ctx_token)


# ── A2A JSON-RPC helpers ──────────────────────────────────────────────────────

async def _handle_message_send(params: dict, req_id: Any) -> JSONResponse:
    """
    Handle message/send.

    Two modes:
    1. New task:  message has no taskId → create task and start background run.
    2. Resume:    message has taskId    → unblock the waiting task with user's response.
    """
    message = params.get("message", {})
    parts   = message.get("parts", [])

    # ── Resume path: taskId present means the caller is resuming a paused task ──
    task_id_resume = (
        message.get("taskId")
        or (params.get("metadata") or {}).get("task_id")
    )
    if task_id_resume:
        task = _a2a_tasks.get(task_id_resume)
        if not task:
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {"code": -32602, "message": f"Task not found: {task_id_resume}"},
                "id": req_id,
            })
        if task.status != "input-required":
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32602,
                    "message": f"Task {task_id_resume} is not waiting for input (status={task.status})",
                },
                "id": req_id,
            })

        task.resume_data = _parse_resume_data(parts)
        logger.info(
            "A2A task %s resumed — resume_keys=%s",
            task_id_resume,
            list(task.resume_data.keys()),
        )
        task.pause_event.set()  # unblock the waiting callback

        return JSONResponse({
            "jsonrpc": "2.0",
            "result": {"id": task_id_resume, "status": {"state": "working"}},
            "id": req_id,
        })

    # ── New task path ──────────────────────────────────────────────────────────
    query = ""
    opts: dict = {}
    # session_id from SuperAgent params.metadata → used as tenant_id for multi-tenancy
    a2a_session_id = (params.get("metadata") or {}).get("session_id", "")
    for part in parts:
        if part.get("kind") == "text":
            query = part.get("text", "")
        elif part.get("kind") == "data":
            blob = part.get("data") or {}
            if isinstance(blob, dict):
                opts = {**opts, **blob}

    # Inject session_id as tenant_id when the caller didn't set one explicitly
    if a2a_session_id and not opts.get("tenant_id"):
        opts = {**opts, "tenant_id": a2a_session_id}

    # When the superagent sends a structured JSON query (e.g. {"search_query": "...",
    # "email_message": "...", "num_leads": 5}), unpack it into the query string and opts
    # so parameters like send_outreach_email and max_leads are honoured.
    try:
        parsed_query = json.loads(query)
        if isinstance(parsed_query, dict) and "search_query" in parsed_query:
            if parsed_query.get("num_leads") and not opts.get("max_leads"):
                opts = {**opts, "max_leads": int(parsed_query["num_leads"])}
            email_msg = parsed_query.get("email_message", "").strip()
            if email_msg and not opts.get("send_outreach_email"):
                opts = {**opts, "send_outreach_email": True}
            # Reconstruct a natural-language query the LLM can act on
            query_parts = [parsed_query["search_query"]]
            if email_msg:
                query_parts.append(f"Use this exact email message template when sending outreach: {email_msg}")
            query = "\n".join(query_parts)
    except (json.JSONDecodeError, ValueError, TypeError):
        pass

    # Infer send_outreach_email from plain-language keywords when not explicitly set
    if not opts.get("send_outreach_email"):
        _send_kws = ["send email", "send outreach", "email them", "reach out", "outreach email",
                     "draft email", "send a message", "contact them", "email the leads"]
        if any(kw in query.lower() for kw in _send_kws):
            opts = {**opts, "send_outreach_email": True}
            logger.info("send_outreach_email inferred True from query keywords")

    if not query:
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {"code": -32602, "message": "No query text found in message parts"},
            "id": req_id,
        })

    task_id = str(uuid.uuid4())
    _a2a_tasks[task_id] = A2ATask(id=task_id, status="submitted")

    asyncio.create_task(_run_agent_task(task_id, query, opts))

    logger.info("A2A task %s submitted — query='%.80s'", task_id, query)
    return JSONResponse({
        "jsonrpc": "2.0",
        "result": {"id": task_id, "status": {"state": "submitted"}},
        "id": req_id,
    })


async def _handle_tasks_get(params: dict, req_id: Any) -> JSONResponse:
    """Handle tasks/get — return current task state including interrupt metadata."""
    task_id = params.get("id", "")
    task = _a2a_tasks.get(task_id)

    if not task:
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {"code": -32602, "message": f"Task not found: {task_id}"},
            "id": req_id,
        })

    result: dict[str, Any] = {
        "id": task_id,
        "status": {"state": task.status},
    }

    # Include interrupt metadata in the status message so a2a_handler can classify it.
    if task.status == "input-required" and task.interrupt_meta:
        result["status"]["message"] = {
            "parts": [{"kind": "text", "text": task.message or "Input required."}],
            "metadata": task.interrupt_meta,
        }
    elif task.message:
        result["status"]["message"] = task.message

    if task.artifacts:
        result["artifacts"] = task.artifacts

    return JSONResponse({"jsonrpc": "2.0", "result": result, "id": req_id})


# ── Endpoints ─────────────────────────────────────────────────────────────────

def _crm_options_list() -> list[str]:
    return list(SUPPORTED_CRM_OPTIONS)


def _tool_settings_schema(base_url: str) -> list[dict[str, Any]]:
    return [
        {
            "tool": "crm_select",
            "kind": "selector",
            "actions": ["set"],
            "options": _crm_options_list(),
            "description": "Set active CRM backend for this tenant.",
        },
        {
            "tool": "hubspot",
            "kind": "token",
            "actions": ["connect", "disconnect"],
            "required_fields": {"connect": ["token"]},
            "description": "HubSpot Private App Token for CRM write.",
            "connect_endpoint": f"{base_url}/crm/hubspot/connect",
        },
        {
            "tool": "gmail",
            "kind": "oauth",
            "actions": ["connect"],
            "required_fields": {"connect": []},
            "description": "Gmail OAuth for sending outreach emails.",
            "connect_endpoint": f"{base_url}/oauth/gmail/connect",
        },
        {
            "tool": "gsheets",
            "kind": "oauth",
            "actions": ["connect"],
            "required_fields": {"connect": ["spreadsheet_id"]},
            "description": "Google Sheets OAuth for CRM export.",
            "connect_endpoint": f"{base_url}/oauth/gsheets/connect",
        },
        {
            "tool": "notion",
            "kind": "oauth_or_pat",
            "actions": ["connect_oauth", "connect_pat", "disconnect"],
            "required_fields": {
                "connect_oauth": ["database_id"],
                "connect_pat": ["token", "database_id"],
            },
            "description": "Notion integration via OAuth or internal token.",
            "connect_endpoint": f"{base_url}/oauth/notion/connect",
            "pat_endpoint": f"{base_url}/crm/notion/connect",
        },
        {
            "tool": "excel",
            "kind": "oauth",
            "actions": ["connect", "disconnect"],
            "required_fields": {"connect": ["workbook_name"]},
            "description": "Microsoft Excel OAuth for CRM export.",
            "connect_endpoint": f"{base_url}/oauth/excel/connect",
        },
    ]


async def _status_hubspot(tenant_id: str) -> dict[str, Any]:
    token = await key_manager.get_hubspot_token(tenant_id)
    return {"connected": bool(token)}


async def _status_gmail(tenant_id: str) -> dict[str, Any]:
    email = await get_sender_email(tenant_id, key_manager.store)
    return {"connected": bool(email), "email": email}


async def _status_gsheets(tenant_id: str) -> dict[str, Any]:
    connected = await gsheets_is_connected(tenant_id, key_manager.store)
    sid = await get_spreadsheet_id(tenant_id, key_manager.store)
    return {"connected": connected, "spreadsheet_id": sid}


async def _status_notion(tenant_id: str) -> dict[str, Any]:
    connected = await notion_is_connected(tenant_id, key_manager.store)
    db_id = await notion_get_db_id(tenant_id, key_manager.store)
    return {"connected": connected, "database_id": db_id}


async def _status_excel(tenant_id: str) -> dict[str, Any]:
    connected = await excel_is_connected(tenant_id, key_manager.store)
    workbook = await excel_get_workbook_name(tenant_id, key_manager.store)
    return {"connected": connected, "workbook_name": workbook}


async def _configure_crm_select(tenant_id: str, action: str, cfg: dict[str, Any]) -> dict[str, Any]:
    if action != "set":
        return {"error": "Unsupported action for crm_select"}
    crm_type = str(cfg.get("crm_type", "")).strip().lower()
    if crm_type not in SUPPORTED_CRM_OPTIONS:
        return {"error": f"Invalid crm_type. Allowed: {', '.join(SUPPORTED_CRM_OPTIONS)}"}
    await key_manager.set_crm_type(tenant_id, crm_type)
    return {"status": "updated", "tenant_id": tenant_id, "crm_type": crm_type}


async def _configure_hubspot(tenant_id: str, action: str, cfg: dict[str, Any]) -> dict[str, Any]:
    if action == "connect":
        token = str(cfg.get("token", "")).strip()
        if not token:
            return {"error": "token is required"}
        await key_manager.store_hubspot_token(tenant_id, token)
        return {"status": "connected", "tool": "hubspot", "tenant_id": tenant_id}
    if action == "disconnect":
        await key_manager.delete_hubspot_token(tenant_id)
        return {"status": "disconnected", "tool": "hubspot", "tenant_id": tenant_id}
    return {"error": "Unsupported action for hubspot"}


async def _configure_gmail(tenant_id: str, action: str, cfg: dict[str, Any]) -> dict[str, Any]:
    if action != "connect":
        return {"error": "Unsupported action for gmail"}
    return {"auth_url": gmail_auth_url(tenant_id), "tenant_id": tenant_id}


async def _configure_gsheets(tenant_id: str, action: str, cfg: dict[str, Any]) -> dict[str, Any]:
    if action != "connect":
        return {"error": "Unsupported action for gsheets"}
    spreadsheet_id = str(cfg.get("spreadsheet_id", "")).strip()
    return {
        "auth_url": gsheets_auth_url(tenant_id, spreadsheet_id, None),
        "tenant_id": tenant_id,
        "spreadsheet_id": spreadsheet_id,
    }


async def _configure_notion(tenant_id: str, action: str, cfg: dict[str, Any]) -> dict[str, Any]:
    if action == "connect_oauth":
        database_id = str(cfg.get("database_id", "")).strip()
        return {
            "auth_url": notion_auth_url(tenant_id, database_id, None),
            "tenant_id": tenant_id,
            "database_id": database_id,
        }
    if action == "connect_pat":
        token = str(cfg.get("token", "")).strip()
        database_id = str(cfg.get("database_id", "")).strip()
        if not token or not database_id:
            return {"error": "token and database_id are required"}
        await key_manager.store_notion_token(tenant_id, token, database_id)
        return {"status": "connected", "tool": "notion", "tenant_id": tenant_id, "database_id": database_id}
    if action == "disconnect":
        await key_manager.delete_notion_token(tenant_id)
        return {"status": "disconnected", "tool": "notion", "tenant_id": tenant_id}
    return {"error": "Unsupported action for notion"}


async def _configure_excel(tenant_id: str, action: str, cfg: dict[str, Any]) -> dict[str, Any]:
    if action == "connect":
        workbook_name = str(cfg.get("workbook_name", "Leads")).strip() or "Leads"
        return {
            "auth_url": excel_auth_url(tenant_id, workbook_name, None),
            "tenant_id": tenant_id,
            "workbook_name": workbook_name,
        }
    if action == "disconnect":
        await excel_delete_tokens(tenant_id, key_manager.store)
        if await key_manager.get_crm_type(tenant_id) == "excel":
            await key_manager.set_crm_type(tenant_id, "")
        return {"status": "disconnected", "tool": "excel", "tenant_id": tenant_id}
    return {"error": "Unsupported action for excel"}


TOOL_INTEGRATION_REGISTRY: dict[str, dict[str, Any]] = {
    "hubspot": {"status": _status_hubspot, "configure": _configure_hubspot},
    "gmail": {"status": _status_gmail, "configure": _configure_gmail},
    "gsheets": {"status": _status_gsheets, "configure": _configure_gsheets},
    "notion": {"status": _status_notion, "configure": _configure_notion},
    "excel": {"status": _status_excel, "configure": _configure_excel},
    "crm_select": {"configure": _configure_crm_select},
}


async def _tool_settings_status(tenant_id: str) -> dict[str, Any]:
    crm_type = await key_manager.get_crm_type(tenant_id)
    tools_state: dict[str, Any] = {}
    for tool_name, adapter in TOOL_INTEGRATION_REGISTRY.items():
        status_fn = adapter.get("status")
        if status_fn:
            tools_state[tool_name] = await status_fn(tenant_id)
    return {
        "tenant_id": tenant_id,
        "active_crm": crm_type,
        "tools": tools_state,
    }


@app.get("/tool-settings/schema", tags=["Tool Settings"])
async def tool_settings_schema():
    base_url = os.getenv("AGENT_BASE_URL", "http://localhost:4567").rstrip("/")
    return JSONResponse({"tools": _tool_settings_schema(base_url)})


@app.get("/tool-settings/status", tags=["Tool Settings"])
async def tool_settings_status(tenant_id: str = "default"):
    return JSONResponse(await _tool_settings_status(tenant_id))


@app.post("/tool-settings/configure", tags=["Tool Settings"])
async def tool_settings_configure(body: ToolSettingsRequest):
    tenant_id = body.tenant_id or "default"
    tool = body.tool.strip().lower()
    action = body.action.strip().lower()
    cfg = body.config or {}
    adapter = TOOL_INTEGRATION_REGISTRY.get(tool)
    if not adapter or not adapter.get("configure"):
        return JSONResponse({"error": f"Unsupported tool/action: {tool}/{action}"}, status_code=400)
    result = await adapter["configure"](tenant_id, action, cfg)
    if isinstance(result, dict) and result.get("error"):
        return JSONResponse(result, status_code=400)
    return JSONResponse(result)


@app.get("/tool-settings/ui", tags=["Tool Settings"])
async def tool_settings_ui():
    html = """<!doctype html>
<html><head><meta charset="utf-8"><title>Lead Gen Tool Settings</title>
<style>body{font-family:Arial,sans-serif;max-width:980px;margin:24px auto;padding:0 12px}button{margin:4px 6px 4px 0}input,select{margin:4px 6px 4px 0;padding:6px}pre{background:#f6f8fa;padding:12px;border-radius:8px;white-space:pre-wrap}</style>
</head><body>
<h2>Lead Gen Tool Settings</h2>
<p>Configure all user-required integrations from one page.</p>
<label>Tenant ID <input id="tenant" value="default"/></label>
<button onclick="refreshAll()">Refresh</button>
<h3>Status</h3><pre id="status">Loading...</pre>
<h3>Quick Actions</h3>
<div>
  <label>Active CRM</label>
  <select id="crm"><option>hubspot</option><option>gsheets</option><option>notion</option><option>excel</option></select>
  <button onclick="setCrm()">Set CRM</button>
</div>
<div>
  <label>HubSpot PAT</label><input id="hubspot_token" placeholder="pat-..."/>
  <button onclick="hubspotConnect()">Connect HubSpot</button>
  <button onclick="hubspotDisconnect()">Disconnect HubSpot</button>
</div>
<div>
  <label>Sheets ID</label><input id="sheet_id" placeholder="spreadsheet id"/>
  <button onclick="oauth('gsheets',{spreadsheet_id:gid('sheet_id').value})">Connect Google Sheets</button>
</div>
<div>
  <button onclick="oauth('gmail',{})">Connect Gmail</button>
</div>
<div>
  <label>Notion DB</label><input id="notion_db" placeholder="database id"/>
  <button onclick="oauth('notion',{database_id:gid('notion_db').value},'connect_oauth')">Connect Notion OAuth</button>
</div>
<div>
  <label>Excel Workbook</label><input id="excel_wb" value="Leads"/>
  <button onclick="oauth('excel',{workbook_name:gid('excel_wb').value})">Connect Excel</button>
</div>
<h3>Schema</h3><pre id="schema">Loading...</pre>
<script>
const gid=(id)=>document.getElementById(id);
async function api(path,method='GET',body=null){const r=await fetch(path,{method,headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):null});return await r.json();}
async function refreshAll(){
  const t=gid('tenant').value||'default';
  gid('status').textContent=JSON.stringify(await api('/tool-settings/status?tenant_id='+encodeURIComponent(t)),null,2);
  gid('schema').textContent=JSON.stringify(await api('/tool-settings/schema'),null,2);
}
async function configure(tool,action,config){const t=gid('tenant').value||'default';return await api('/tool-settings/configure','POST',{tenant_id:t,tool,action,config});}
async function setCrm(){alert(JSON.stringify(await configure('crm_select','set',{crm_type:gid('crm').value}),null,2));await refreshAll();}
async function hubspotConnect(){alert(JSON.stringify(await configure('hubspot','connect',{token:gid('hubspot_token').value}),null,2));await refreshAll();}
async function hubspotDisconnect(){alert(JSON.stringify(await configure('hubspot','disconnect',{}),null,2));await refreshAll();}
async function oauth(tool,config,action='connect'){const data=await configure(tool,action,config);if(data.auth_url){window.open(data.auth_url,'_blank');}alert(JSON.stringify(data,null,2));await refreshAll();}
refreshAll();
</script></body></html>"""
    return HTMLResponse(html)

@app.get("/.well-known/agent.json", tags=["A2A Discovery"])
async def agent_card_standard():
    return JSONResponse(_load_agent_card())


@app.get("/.well-known/agent-card", tags=["A2A Discovery"])
async def agent_card_legacy():
    return JSONResponse(_load_agent_card())


_send_rate: dict[str, list[float]] = {}  # ip → timestamps of recent message/send calls

def _check_send_rate(ip: str, limit: int = 30) -> bool:
    """Return True if ip is within `limit` message/send calls per minute."""
    now = asyncio.get_event_loop().time()
    window = _send_rate.setdefault(ip, [])
    _send_rate[ip] = [t for t in window if now - t < 60]
    if len(_send_rate[ip]) >= limit:
        return False
    _send_rate[ip].append(now)
    return True


@app.post("/", tags=["A2A"])
async def a2a_jsonrpc(
    request: Request,
    _auth=Depends(verify_api_key),
):
    """
    A2A JSON-RPC endpoint.
    Supported methods: message/send, tasks/get

    Rate limiting applies only to message/send (new task creation).
    tasks/get is exempt — it is a status-polling call and must not be throttled.
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {"code": -32700, "message": "Parse error: invalid JSON"},
            "id": None,
        }, status_code=400)

    method  = body.get("method", "")
    req_id  = body.get("id")
    params  = body.get("params", {})

    logger.info("A2A JSON-RPC: method=%s id=%s", method, req_id)

    if method == "message/send":
        ip = get_remote_address(request)
        if not _check_send_rate(ip):
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": "Rate limit exceeded — retry after 60 s"},
                "id": req_id,
            }, status_code=429)
        return await _handle_message_send(params, req_id)
    elif method == "tasks/get":
        return await _handle_tasks_get(params, req_id)
    else:
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {"code": -32601, "message": f"Method not found: {method!r}"},
            "id": req_id,
        }, status_code=200)



@app.post("/crm/hubspot/connect", tags=["CRM"])
async def hubspot_connect(request: Request):
    """
    Save a client's HubSpot Private App Token.
    Body: {"tenant_id": "abc", "token": "pat-na1-..."}
    After connecting, the agent will never ask for the token again.
    """
    body = await request.json()
    tenant_id = body.get("tenant_id", "default")
    token     = (body.get("token") or "").strip()
    if not token or len(token) < 10:
        return JSONResponse({"error": "Invalid token — must be at least 10 characters"}, status_code=400)
    await key_manager.store_hubspot_token(tenant_id, token)
    logger.info("HubSpot token stored for tenant %s", tenant_id)
    return JSONResponse({"status": "connected", "crm": "hubspot", "tenant_id": tenant_id})


@app.get("/crm/hubspot/status", tags=["CRM"])
async def hubspot_status(tenant_id: str = "default"):
    """Check whether a tenant has a stored HubSpot token."""
    token = await key_manager.get_hubspot_token(tenant_id)
    return JSONResponse({"connected": bool(token), "crm": "hubspot", "tenant_id": tenant_id})


@app.delete("/crm/hubspot/disconnect", tags=["CRM"])
async def hubspot_disconnect(tenant_id: str = "default"):
    """Remove a tenant's HubSpot token."""
    await key_manager.delete_hubspot_token(tenant_id)
    return JSONResponse({"status": "disconnected", "crm": "hubspot", "tenant_id": tenant_id})


@app.get("/oauth/gmail/connect", tags=["OAuth"])
async def gmail_connect(tenant_id: str = "default", task_id: str | None = None):
    """
    Start Gmail OAuth flow.

    Design A (pre-auth):  GET /oauth/gmail/connect?tenant_id=abc
    Design B (mid-task):  Called automatically via interrupt; auth_url already embeds task_id.

    Terminal test:
        curl "http://localhost:4567/oauth/gmail/connect?tenant_id=mycompany"
        → copy the auth_url, open in browser
    """
    if not os.getenv("GOOGLE_CLIENT_ID"):
        return JSONResponse(
            {"error": "GOOGLE_CLIENT_ID not set. Add it to .env from Google Cloud Console."},
            status_code=503,
        )
    auth_url = gmail_auth_url(tenant_id, task_id)
    return JSONResponse({"auth_url": auth_url, "tenant_id": tenant_id, "task_id": task_id})


@app.get("/oauth/gmail/callback", tags=["OAuth"])
async def gmail_callback(
    state: str | None = None,
    code:  str | None = None,
    error: str | None = None,
):
    """
    Google redirects here after user authorises Gmail access.
    state = "tenant_id" or "tenant_id:task_id"

    If task_id is present, the waiting agent task is auto-resumed — no super-agent
    intervention needed. Super-agent just keeps polling tasks/get.
    """
    if error or not code or not state:
        logger.error("Gmail OAuth callback error: error=%s code_present=%s state=%s", error, bool(code), state)
        return JSONResponse(
            {"error": error or "missing_code", "hint": "Google did not return an auth code — check the OAuth app's authorized redirect URIs and scopes in Google Cloud Console."},
            status_code=400,
        )

    parts     = state.split(":", 1)
    tenant_id = parts[0]
    task_id   = parts[1] if len(parts) > 1 else None

    try:
        token_data   = await gmail_exchange_code(code)
        sender_email = await gmail_store_tokens(tenant_id, token_data, key_manager.store)
        logger.info("Gmail OAuth complete: tenant=%s email=%s task=%s", tenant_id, sender_email, task_id)
    except Exception as exc:
        logger.error("Gmail OAuth callback failed: %s", exc)
        return JSONResponse({"error": str(exc)}, status_code=400)

    # Auto-resume the paused task if task_id was embedded in state (Design B)
    if task_id and task_id in _a2a_tasks:
        task = _a2a_tasks[task_id]
        if task.status == "input-required":
            task.pause_event.set()
            logger.info("Auto-resumed task %s after Gmail OAuth", task_id)

    return HTMLResponse("""<!DOCTYPE html>
<html><head><title>Gmail Connected</title></head>
<body style="font-family:sans-serif;text-align:center;padding:40px">
  <h2>✓ Gmail connected</h2>
  <p>This window will close automatically…</p>
  <script>window.close();</script>
</body></html>""")


@app.get("/oauth/gmail/status", tags=["OAuth"])
async def gmail_status(tenant_id: str = "default"):
    """Check whether a tenant has a stored Gmail token."""
    email = await get_sender_email(tenant_id, key_manager.store)
    return JSONResponse({"connected": bool(email), "email": email, "tenant_id": tenant_id})


@app.get("/oauth/gsheets/connect", tags=["OAuth"])
async def gsheets_connect(
    tenant_id: str = "default",
    spreadsheet_id: str = "",
    task_id: str | None = None,
):
    """
    Start Google Sheets OAuth flow.

    spreadsheet_id: the client's Google Sheet ID
      (from the URL: docs.google.com/spreadsheets/d/<spreadsheet_id>/edit)
    After authorising, the agent can read/write leads to that sheet.
    """
    if not os.getenv("GOOGLE_CLIENT_ID"):
        return JSONResponse({"error": "GOOGLE_CLIENT_ID not set"}, status_code=503)
    auth_url = gsheets_auth_url(tenant_id, spreadsheet_id, task_id)
    return JSONResponse({
        "auth_url":       auth_url,
        "tenant_id":      tenant_id,
        "spreadsheet_id": spreadsheet_id,
        "task_id":        task_id,
    })


@app.get("/oauth/gsheets/callback", tags=["OAuth"])
async def gsheets_callback(
    state: str | None = None,
    code:  str | None = None,
    error: str | None = None,
):
    """
    Google redirects here after the user authorises Sheets access.
    state encodes tenant_id, spreadsheet_id, and optional task_id.
    """
    if error or not code or not state:
        return JSONResponse(
            {"error": error or "missing_code",
             "hint": "Check the OAuth app's authorized redirect URIs include /oauth/gsheets/callback"},
            status_code=400,
        )

    import json as _json
    try:
        state_data     = _json.loads(state)
        tenant_id      = state_data.get("t", "default")
        spreadsheet_id = state_data.get("s", "")
        task_id        = state_data.get("tid")
    except Exception:
        # Fallback: treat state as plain tenant_id
        tenant_id, spreadsheet_id, task_id = state, "", None

    try:
        token_data = await gsheets_exchange_code(code)
        await gsheets_store_tokens(tenant_id, token_data, spreadsheet_id, key_manager.store)
        await key_manager.set_crm_type(tenant_id, "gsheets")
        logger.info("Sheets OAuth complete: tenant=%s sheet=%s task=%s", tenant_id, spreadsheet_id, task_id)
    except Exception as exc:
        logger.error("Sheets OAuth callback failed: %s", exc)
        return JSONResponse({"error": str(exc)}, status_code=400)

    if task_id and task_id in _a2a_tasks:
        task = _a2a_tasks[task_id]
        if task.status == "input-required":
            task.pause_event.set()
            logger.info("Auto-resumed task %s after Sheets OAuth", task_id)

    return HTMLResponse("""<!DOCTYPE html>
<html><head><title>Google Sheets Connected</title></head>
<body style="font-family:sans-serif;text-align:center;padding:40px">
  <h2>✓ Google Sheets connected</h2>
  <p>This window will close automatically…</p>
  <script>window.close();</script>
</body></html>""")


@app.get("/oauth/gsheets/status", tags=["OAuth"])
async def gsheets_status(tenant_id: str = "default"):
    """Check whether a tenant has a stored Google Sheets token."""
    connected = await gsheets_is_connected(tenant_id, key_manager.store)
    sid = await get_spreadsheet_id(tenant_id, key_manager.store)
    return JSONResponse({
        "connected":      connected,
        "crm":            "gsheets",
        "spreadsheet_id": sid,
        "tenant_id":      tenant_id,
    })


@app.get("/oauth/notion/connect", tags=["OAuth"])
async def notion_connect(
    tenant_id: str = "default",
    database_id: str = "",
    task_id: str | None = None,
):
    """
    Start Notion OAuth flow (public integration).
    database_id: the Notion database where leads will be written.
    For internal integration tokens, use POST /crm/notion/connect instead.
    """
    client_id = os.getenv("NOTION_CLIENT_ID")
    if not client_id:
        return JSONResponse({"error": "NOTION_CLIENT_ID not set"}, status_code=503)
    auth_url = notion_auth_url(tenant_id, database_id, task_id)
    return JSONResponse({
        "auth_url":    auth_url,
        "tenant_id":   tenant_id,
        "database_id": database_id,
        "task_id":     task_id,
    })


@app.get("/oauth/notion/callback", tags=["OAuth"])
async def notion_callback(
    code:  str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    """Notion redirects here after the user authorises access."""
    if error or not code or not state:
        return JSONResponse(
            {"error": error or "missing_code",
             "hint": "Check NOTION_REDIRECT_URI in .env matches what is set in the Notion integration."},
            status_code=400,
        )

    import json as _json
    try:
        state_data  = _json.loads(state)
        tenant_id   = state_data.get("t", "default")
        database_id = state_data.get("d", "")
        task_id     = state_data.get("tid")
    except Exception:
        tenant_id, database_id, task_id = state, "", None

    try:
        token_data = await notion_exchange_code(code)
        # Notion OAuth returns workspace_id and bot_id in addition to access_token
        # Store the access token with the provided database_id only.
        # workspace_id is NOT a Notion database ID and must not be used as one.
        await notion_store_pat(
            tenant_id,
            token_data["access_token"],
            database_id,  # Empty string if not provided; user must set it separately
            key_manager.store,
        )
        await key_manager.set_crm_type(tenant_id, "notion")
        logger.info("Notion OAuth complete: tenant=%s db=%r task=%s", tenant_id, database_id, task_id)
    except Exception as exc:
        logger.error("Notion OAuth callback failed: %s", exc)
        return JSONResponse({"error": str(exc)}, status_code=400)

    if task_id and task_id in _a2a_tasks:
        task = _a2a_tasks[task_id]
        if task.status == "input-required":
            task.pause_event.set()
            logger.info("Auto-resumed task %s after Notion OAuth", task_id)

    return JSONResponse({
        "status":      "connected",
        "crm":         "notion",
        "database_id": database_id,
        "tenant_id":   tenant_id,
        "task_resumed": bool(task_id and task_id in _a2a_tasks),
        "message":     "Notion connected. You can close this tab.",
    })


@app.get("/oauth/notion/status", tags=["OAuth"])
async def notion_status(tenant_id: str = "default"):
    """Check whether a tenant has a stored Notion token."""
    connected = await notion_is_connected(tenant_id, key_manager.store)
    db_id = await notion_get_db_id(tenant_id, key_manager.store)
    return JSONResponse({
        "connected":   connected,
        "crm":         "notion",
        "database_id": db_id,
        "tenant_id":   tenant_id,
    })


@app.post("/crm/notion/connect", tags=["CRM"])
async def notion_pat_connect(request: Request):
    """
    Save a Notion internal integration token (PAT) + database ID.
    Use this for private/internal Notion integrations (no OAuth redirect needed).
    Body: {"tenant_id": "abc", "token": "secret_...", "database_id": "xxx"}
    """
    body = await request.json()
    tenant_id   = body.get("tenant_id", "default")
    token       = (body.get("token") or "").strip()
    database_id = (body.get("database_id") or "").strip()

    if not token or len(token) < 10:
        return JSONResponse({"error": "Invalid token"}, status_code=400)
    if not database_id:
        return JSONResponse({"error": "database_id is required"}, status_code=400)

    await key_manager.store_notion_token(tenant_id, token, database_id)
    logger.info("Notion PAT stored for tenant %s (db=%s)", tenant_id, database_id)
    return JSONResponse({"status": "connected", "crm": "notion", "tenant_id": tenant_id, "database_id": database_id})


@app.delete("/crm/notion/disconnect", tags=["CRM"])
async def notion_disconnect(tenant_id: str = "default"):
    """Remove a tenant's Notion token."""
    await key_manager.delete_notion_token(tenant_id)
    return JSONResponse({"status": "disconnected", "crm": "notion", "tenant_id": tenant_id})


@app.get("/oauth/excel/connect", tags=["OAuth"])
async def excel_connect(
    tenant_id: str = "default",
    workbook_name: str = "Leads",
    task_id: str | None = None,
):
    """
    Start Microsoft Excel OAuth flow.
    workbook_name: name of the OneDrive Excel workbook to use (default: Leads).
    The workbook will be created in the user's OneDrive root if it doesn't exist.
    """
    client_id = os.getenv("MICROSOFT_CLIENT_ID")
    if not client_id:
        return JSONResponse({"error": "MICROSOFT_CLIENT_ID not set"}, status_code=503)
    auth_url = excel_auth_url(tenant_id, workbook_name, task_id)
    return JSONResponse({
        "auth_url":      auth_url,
        "tenant_id":     tenant_id,
        "workbook_name": workbook_name,
        "task_id":       task_id,
    })


@app.get("/oauth/excel/callback", tags=["OAuth"])
async def excel_callback(
    code:  str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    """Microsoft redirects here after the user authorises OneDrive/Excel access."""
    if error or not code or not state:
        return JSONResponse(
            {"error": error or "missing_code",
             "hint": "Check EXCEL_REDIRECT_URI in .env matches your Azure app registration."},
            status_code=400,
        )

    import json as _json
    try:
        state_data    = _json.loads(state)
        tenant_id     = state_data.get("t", "default")
        workbook_name = state_data.get("w", "Leads")
        task_id       = state_data.get("tid")
    except Exception:
        tenant_id, workbook_name, task_id = state, "Leads", None

    try:
        token_data = await excel_exchange_code(code)
        await excel_store_tokens(tenant_id, token_data, workbook_name, key_manager.store)
        await key_manager.set_crm_type(tenant_id, "excel")
        logger.info("Excel OAuth complete: tenant=%s workbook=%s task=%s", tenant_id, workbook_name, task_id)
    except Exception as exc:
        logger.error("Excel OAuth callback failed: %s", exc)
        return JSONResponse({"error": str(exc)}, status_code=400)

    if task_id and task_id in _a2a_tasks:
        task = _a2a_tasks[task_id]
        if task.status == "input-required":
            task.pause_event.set()
            logger.info("Auto-resumed task %s after Excel OAuth", task_id)

    return JSONResponse({
        "status":        "connected",
        "crm":           "excel",
        "workbook_name": workbook_name,
        "tenant_id":     tenant_id,
        "task_resumed":  bool(task_id and task_id in _a2a_tasks),
        "message":       "Microsoft Excel connected. You can close this tab.",
    })


@app.get("/oauth/excel/status", tags=["OAuth"])
async def excel_status(tenant_id: str = "default"):
    """Check whether a tenant has a stored Excel/OneDrive token."""
    connected = await excel_is_connected(tenant_id, key_manager.store)
    workbook  = await excel_get_workbook_name(tenant_id, key_manager.store)
    return JSONResponse({
        "connected":     connected,
        "crm":           "excel",
        "workbook_name": workbook,
        "tenant_id":     tenant_id,
    })


@app.delete("/oauth/excel/disconnect", tags=["OAuth"])
async def excel_disconnect(tenant_id: str = "default"):
    """Remove a tenant's Excel/OneDrive token."""
    await excel_delete_tokens(tenant_id, key_manager.store)
    crm = await key_manager.get_crm_type(tenant_id)
    if crm == "excel":
        await key_manager.set_crm_type(tenant_id, "")
    return JSONResponse({"status": "disconnected", "crm": "excel", "tenant_id": tenant_id})


@app.post("/crm/select", tags=["CRM"])
async def crm_select(request: Request):
    """
    Switch the active CRM for a tenant.
    Body: {"tenant_id": "abc", "crm_type": "hubspot" | "gsheets" | "notion" | "excel"}
    The chosen CRM must already be connected; this just changes which one is active.
    """
    body     = await request.json()
    tenant_id = body.get("tenant_id", "default")
    crm_type  = (body.get("crm_type") or "").lower().strip()

    allowed = set(SUPPORTED_CRM_OPTIONS)
    if crm_type not in allowed:
        return JSONResponse(
            {"error": f"Invalid crm_type. Allowed: {', '.join(sorted(allowed))}"},
            status_code=400,
        )

    await key_manager.set_crm_type(tenant_id, crm_type)
    connected, _ = await key_manager.has_crm_connected(tenant_id)
    return JSONResponse({
        "status":    "updated",
        "crm_type":  crm_type,
        "connected": connected,
        "tenant_id": tenant_id,
        "warning":   None if connected else f"{crm_type} is selected but not yet connected — run the connect flow first.",
    })


@app.get("/crm/status", tags=["CRM"])
async def crm_status(tenant_id: str = "default"):
    """Return which CRM is connected for a tenant and connection details."""
    crm_type = await key_manager.get_crm_type(tenant_id)
    connected, _ = await key_manager.has_crm_connected(tenant_id)
    details: dict = {"crm_type": crm_type, "connected": connected, "tenant_id": tenant_id}
    if crm_type == "hubspot":
        token = await key_manager.get_hubspot_token(tenant_id)
        details["hubspot_connected"] = bool(token)
    elif crm_type == "gsheets":
        details["spreadsheet_id"] = await get_spreadsheet_id(tenant_id, key_manager.store)
    elif crm_type == "notion":
        details["database_id"] = await notion_get_db_id(tenant_id, key_manager.store)
    elif crm_type == "excel":
        details["workbook_name"] = await excel_get_workbook_name(tenant_id, key_manager.store)
    return JSONResponse(details)


@app.post("/run", tags=["Standalone"])
@limiter.limit("5/minute")
async def standalone_run(request: Request, _auth=Depends(verify_api_key)):
    """
    Synchronous standalone endpoint — runs the agent and returns results directly.
    No A2A protocol needed; suitable for direct API calls or testing.

    Body (all fields optional except query):
    {
      "query":               "Find CTOs at Series B SaaS companies in NYC",
      "tenant_id":           "default",
      "max_leads":           20,
      "write_to_crm":        true,
      "send_outreach_email": true
    }

    HITL interrupts (email review, HubSpot auth) are skipped in standalone mode —
    use the A2A endpoint (POST /) for interactive workflows.
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    query     = (body.get("query") or "").strip()
    tenant_id = body.get("tenant_id", "default")

    if not query:
        return JSONResponse({"error": "query is required"}, status_code=400)

    crm_creds = await key_manager.get_crm_credentials(tenant_id)
    crm_type  = crm_creds.get("crm_type")

    try:
        result = await agent.run(
            query=query,
            max_leads=int(body.get("max_leads", 20)),
            write_to_crm=bool(body.get("write_to_crm", True)),
            send_outreach_email=bool(body.get("send_outreach_email", True)),
            tenant_id=tenant_id,
            gmail_token_store=key_manager.store,
            crm_type=crm_type,
            gsheets_token_store=key_manager.store,
            spreadsheet_id=crm_creds.get("spreadsheet_id"),
            notion_token_store=key_manager.store,
            notion_database_id=crm_creds.get("notion_database_id"),
            excel_token_store=key_manager.store,
            excel_workbook_name=crm_creds.get("excel_workbook_name", "Leads"),
        )
        return JSONResponse(result)
    except Exception as exc:
        logger.error("Standalone /run failed: %s", exc, exc_info=True)
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.get("/health", tags=["Ops"])
async def health():
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    active = sum(1 for t in _a2a_tasks.values() if t.status in ("working", "input-required"))
    return {
        "status":         "ok",
        "version":        "1.2.0",
        "agent_ready":    agent is not None,
        "llm_provider":   provider,
        "active_tasks":   active,
        "total_tasks":    len(_a2a_tasks),
        "crm_backends":   ["hubspot", "gsheets", "notion", "excel"],
        "interrupt_support": ["email_draft_review", "hubspot_auth", "gmail_oauth", "gsheets_oauth"],
        "apis_configured": {
            "anthropic":   bool(os.getenv("ANTHROPIC_API_KEY")),
            "openai":      bool(os.getenv("OPENAI_API_KEY")),
            "openrouter":  bool(os.getenv("OPENROUTER_API_KEY")),
            "apollo":      bool(os.getenv("APOLLO_API_KEY")),
            "hunter":      bool(os.getenv("HUNTER_API_KEY")),
            "sendgrid":    bool(os.getenv("SENDGRID_API_KEY")),
            "google_oauth": bool(os.getenv("GOOGLE_CLIENT_ID")),
            "notion_oauth": bool(os.getenv("NOTION_CLIENT_ID")),
            "excel_oauth":  bool(os.getenv("MICROSOFT_CLIENT_ID")),
        },
    }


@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": (
            "Lead Gen Agent v1.1 — "
            "A2A endpoint: POST / | "
            "Discovery: /.well-known/agent.json | "
            "Docs: /docs"
        )
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=4567, reload=True)
