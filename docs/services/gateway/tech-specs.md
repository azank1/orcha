# MetaOrcha Gateway Service — Technical Specification v1.0

## Document Status: Implementation-Ready
**Supersedes:** FE Gateway API Contract (design handoff brief)
**Depends on:** SuperAgent v2.1, Registry Service, PnD Service
**Date:** 2026-04-01

---

## 1. Overview & Responsibility Boundary

The Gateway is the **single ingress point** for all external clients. No client ever speaks directly to SuperAgent, Registry, or PnD.

```
FE / CLI / SDK
      │
      ▼
┌─────────────┐   JWT validation, rate-limiting, session routing,
│   Gateway   │   SSE fan-out, credential proxying, agent registration
│  :8080      │   proxying, workflow persistence, user management
└─────────────┘
      │              │                │
      ▼              ▼                ▼
SuperAgent       Registry         (future)
  :8003            :8000           PnD :8001
```

**Gateway owns:**
- User auth (SASL/JWT issue + validation)
- Session lifecycle (create, route, track)
- SSE stream multiplexing and enrichment (SuperAgent → FE)
- Interrupt relay (FE → SuperAgent resume)
- Credential proxying (FE → SuperAgent VaultService)
- Agent registration proxying (FE → Registry)
- Workflow CRUD (FE → SuperAgent workflow store)
- User settings and developer mode
- Health aggregation across downstream services

**Gateway does NOT own:**
- LangGraph execution (SuperAgent)
- Agent discovery/ranking (PnD)
- Agent manifest storage (Registry)
- Vault encryption (SuperAgent VaultService)

---

## 2. Technology Stack

```
Language:       Python 3.12
Framework:      FastAPI + Uvicorn[standard]
Auth:           python-jose[cryptography] (JWT HS256), passlib[bcrypt]
SSE:            FastAPI StreamingResponse + httpx-sse (for upstream consumption)
DB:             PostgreSQL via asyncpg + Prisma (shared common-database workspace pkg)
Cache/Session:  Redis (aioredis) — session index, rate-limit counters
HTTP clients:   httpx[http2] — for SuperAgent, Registry, PnD calls
Config:         pydantic-settings
Packaging:      uv
Testing:        pytest, pytest-asyncio, respx (mock httpx)
```

**Port:** `8080` (all public traffic)

---

## 3. Directory Structure

```
gateway/
├── pyproject.toml
├── .env
├── .env.example
└── src/
    └── gateway/
        ├── __init__.py
        ├── main.py                  # FastAPI app, lifespan, middleware
        ├── config.py                # pydantic-settings
        ├── dependencies.py          # FastAPI Depends() helpers
        ├── auth/
        │   ├── __init__.py
        │   ├── jwt.py               # token issue + validation
        │   ├── models.py            # User, TokenPayload pydantic models
        │   └── routes.py            # /auth/* endpoints
        ├── sessions/
        │   ├── __init__.py
        │   ├── models.py            # Session, MessageRequest pydantic models
        │   ├── routes.py            # /api/v1/sessions/* endpoints
        │   ├── sse_relay.py         # upstream SSE consumer + enrichment
        │   └── store.py             # Redis session index
        ├── credentials/
        │   ├── __init__.py
        │   ├── models.py
        │   └── routes.py            # /api/v1/credentials/*
        ├── workflows/
        │   ├── __init__.py
        │   ├── models.py
        │   └── routes.py            # /api/v1/workflows/*
        ├── agents/
        │   ├── __init__.py
        │   ├── models.py
        │   └── routes.py            # /api/v1/dev/agents/*
        ├── settings/
        │   ├── __init__.py
        │   ├── models.py
        │   └── routes.py            # /api/v1/settings/*
        └── proxy/
            ├── __init__.py
            ├── superagent.py        # typed async client for SuperAgent
            └── registry.py          # typed async client for Registry
```

---

## 4. Configuration

```python
# src/gateway/config.py

class Settings(BaseSettings):
    # Server
    host: str = "0.0.0.0"
    port: int = 8080
    log_level: str = "info"

    # Auth
    jwt_secret: str               # HS256 signing key — generate: openssl rand -hex 32
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7    # 7 days
    jwt_refresh_expire_days: int = 30

    # Downstream services
    superagent_url: str = "http://localhost:8003"
    registry_url: str   = "http://localhost:8000"
    pnd_url: str        = "http://localhost:8001"

    # Infrastructure
    redis_url: str = "redis://localhost:6379"
    database_url: str

    # Rate limiting (requests per minute per user)
    rate_limit_default: int = 60
    rate_limit_session_message: int = 20

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
```

---

## 5. Auth System

### 5.1 User Model (Postgres via Prisma)

```
model User {
  id           String   @id @default(uuid())
  email        String   @unique
  password_hash String
  display_name String?
  is_dev_mode  Boolean  @default(false)
  credits_usd  Decimal  @default(0)
  created_at   DateTime @default(now())
  updated_at   DateTime @updatedAt
}
```

### 5.2 JWT Payload

```python
class TokenPayload(BaseModel):
    sub: str          # user_id (UUID)
    email: str
    is_dev: bool
    exp: int          # unix timestamp
    iat: int
    jti: str          # unique token ID for revocation
```

### 5.3 Auth Routes — `POST /auth/*`

```
POST /auth/register
  Body:    { email, password, display_name? }
  Returns: { user_id, email, access_token, refresh_token }
  Errors:  409 if email taken

POST /auth/login
  Body:    { email, password }
  Returns: { access_token, refresh_token, user_id, email, is_dev }

POST /auth/refresh
  Body:    { refresh_token }
  Returns: { access_token }

POST /auth/logout
  Header:  Authorization: Bearer <token>
  Action:  Adds jti to Redis revocation set (TTL = remaining token lifetime)
  Returns: 204
```

### 5.4 Auth Middleware

All `/api/v1/*` routes require `Authorization: Bearer <jwt>`.

```python
# src/gateway/dependencies.py

async def require_auth(
    authorization: str = Header(...),
    redis: Redis = Depends(get_redis),
) -> TokenPayload:
    token = authorization.removeprefix("Bearer ").strip()
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    # Check revocation list
    if await redis.sismember("revoked_tokens", payload["jti"]):
        raise HTTPException(401, "Token revoked")
    return TokenPayload(**payload)

async def require_dev_mode(token: TokenPayload = Depends(require_auth)) -> TokenPayload:
    if not token.is_dev:
        raise HTTPException(403, "Developer mode not enabled")
    return token
```

---

## 6. Session Management

### 6.1 Session Store (Redis)

```
Key:   session:{session_id}
Type:  Redis Hash
TTL:   24 hours (refreshed on every message)

Fields:
  user_id         string
  created_at      ISO timestamp
  last_active_at  ISO timestamp
  status          "active" | "interrupted" | "complete" | "error"
  title           string  (set after first agent response, used in sidebar)
  message_count   int
```

### 6.2 Session Routes

```
POST /api/v1/sessions
  Auth:    required
  Body:    { title?: string }
  Action:  1. Create session record in Redis with user_id from JWT
           2. POST /sessions to SuperAgent with { user_id }
           3. Store returned session_id in Redis hash
  Returns: { session_id, created_at, status: "active" }

GET /api/v1/sessions
  Auth:    required
  Returns: [ { session_id, title, created_at, last_active_at, status } ]
  Note:    Lists all sessions for the authenticated user from Redis index

GET /api/v1/sessions/:id/status
  Auth:    required (must own session)
  Action:  Proxies GET /sessions/:id/status to SuperAgent
           Augments with Redis session metadata
  Returns: {
    session_id, status, title, created_at, last_active_at,
    message_count,
    pending_interrupt: { interrupt_id, interrupt_type, message, metadata } | null
  }
```

---

## 7. SSE Stream — The Core Contract

This is the most critical piece. The Gateway consumes SuperAgent's raw SSE stream, enriches each event with a typed `event_class` label, and re-emits it to the FE. The FE's rendering logic keys entirely on `event_class`.

### 7.1 Sending a Message

```
POST /api/v1/sessions/:id/message
  Auth:    required (must own session)
  Body:    { message: string }
  Returns: text/event-stream (SSE)

POST /api/v1/sessions/:id/resume
  Auth:    required (must own session)
  Body:    { interrupt_id: string, resume_value: string }
  Returns: text/event-stream (SSE)
```

Both routes open a streaming response back to the FE while simultaneously consuming the upstream SuperAgent SSE stream via `httpx-sse`.

### 7.2 Upstream SuperAgent Event Types (raw, from runner.py)

The SuperAgent currently emits three raw event types:

```python
{"type": "token",     "content": str}
{"type": "progress",  "content": str}
{"type": "interrupt", "interrupt_id": str, "interrupt_type": str,
                      "message": str, "metadata": dict}
{"type": "done",      "session_id": str}
```

These are **too coarse** for the FE. The Gateway's `SSERelay` enriches them into a richer typed envelope.

### 7.3 Gateway SSE Envelope (emitted to FE)

Every event the FE receives has this shape:

```typescript
interface GatewaySSEEvent {
  // --- Routing & identity ---
  event_class:  EventClass      // primary discriminator for FE rendering
  session_id:   string
  seq:          number          // monotonically increasing per session
  ts:           string          // ISO timestamp

  // --- Payload (varies by event_class) ---
  content?:     string
  metadata?:    Record<string, unknown>
}

type EventClass =
  // ── Message channel ──────────────────────────────────────────────
  | "message.human"       // echoed user message (for FE history sync)
  | "message.ai.token"    // streaming token chunk from LLM
  | "message.ai.done"     // LLM response complete (full content in metadata.full_content)
  | "message.system"      // system-level notice (e.g. "context compressed")

  // ── Thinking / reasoning ─────────────────────────────────────────
  | "thinking.start"      // agent is reasoning (spinner on)
  | "thinking.step"       // progress update: "Discovering agents...", "Calling fetch_emails..."
  | "thinking.done"       // reasoning phase complete

  // ── Tool / agent invocations ──────────────────────────────────────
  | "invocation.start"    // tool call dispatched
                          // metadata: { tool_name, agent_id, protocol, args_preview }
  | "invocation.result"   // tool call returned
                          // metadata: { tool_name, agent_id, duration_ms, result_preview }
  | "invocation.error"    // tool call failed
                          // metadata: { tool_name, error }

  // ── Task checklist ────────────────────────────────────────────────
  | "checklist.created"   // new checklist; metadata: { goal, steps: ChecklistStep[] }
  | "checklist.updated"   // step status changed; metadata: { step_id, status, description }
  | "checklist.done"      // all steps terminal

  // ── Agents (right panel) ──────────────────────────────────────────
  | "agent.discovered"    // new agent added to session cache
                          // metadata: { agent_id, name, protocol, capabilities[] }
  | "agent.active"        // agent is being called right now
  | "agent.idle"          // agent call returned

  // ── Interrupts / HITL ─────────────────────────────────────────────
  | "interrupt.required"  // execution paused; metadata: { interrupt_id, interrupt_type,
                          //   message, agent_id?, metadata{} }
  | "interrupt.resolved"  // user resume accepted, execution continuing

  // ── Artifacts ─────────────────────────────────────────────────────
  | "artifact.created"    // metadata: { artifact_id, mime_type, description, download_url }

  // ── Session lifecycle ─────────────────────────────────────────────
  | "session.started"     // first event of every stream
  | "session.complete"    // all work done
  | "session.error"       // unrecoverable error; metadata: { error }

  // ── Token / billing meta ──────────────────────────────────────────
  | "meta.usage"          // metadata: { estimated_tokens, credits_usd }
```

### 7.4 SSERelay Implementation Spec

```python
# src/gateway/sessions/sse_relay.py

class SSERelay:
    """
    Consumes raw SuperAgent SSE stream, transforms events into
    typed GatewaySSEEvent envelopes, and yields JSON-serialised SSE lines.
    """

    def __init__(self, session_id: str, user_message: str | None = None):
        self._session_id = session_id
        self._user_message = user_message
        self._seq = 0
        self._token_buffer: list[str] = []   # accumulates streaming tokens

    def _emit(self, event_class: str, content: str = "", metadata: dict = {}) -> str:
        self._seq += 1
        envelope = {
            "event_class": event_class,
            "session_id":  self._session_id,
            "seq":         self._seq,
            "ts":          datetime.utcnow().isoformat(),
            "content":     content,
            "metadata":    metadata,
        }
        return f"data: {json.dumps(envelope)}\n\n"

    async def relay(
        self,
        upstream_url: str,
        upstream_body: dict,
        httpx_client: httpx.AsyncClient,
    ) -> AsyncIterator[str]:

        # Always open with session.started + echo human message
        yield self._emit("session.started")
        if self._user_message:
            yield self._emit("message.human", content=self._user_message)
        yield self._emit("thinking.start")

        async with httpx_client.stream("POST", upstream_url, json=upstream_body) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data:"):
                    continue
                raw = line[5:].strip()
                if not raw:
                    continue
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                async for translated in self._translate(event):
                    yield translated

        # Flush any remaining token buffer
        if self._token_buffer:
            full = "".join(self._token_buffer)
            self._token_buffer.clear()
            yield self._emit("message.ai.done", metadata={"full_content": full})

    async def _translate(self, event: dict) -> AsyncIterator[str]:
        t = event.get("type", "")

        if t == "token":
            content = event.get("content", "")
            self._token_buffer.append(content)
            # First token: signal thinking done + invocation result
            if len(self._token_buffer) == 1:
                yield self._emit("thinking.done")
            yield self._emit("message.ai.token", content=content)

        elif t == "progress":
            content = event.get("content", "")
            # Heuristic enrichment from progress strings
            # SuperAgent emits progress messages like:
            #   "Calling fetch_emails..."
            #   "Discovering agents for your task..."
            #   "Checklist created: ..."
            #   "Step complete: ..."
            yield from self._enrich_progress(content)

        elif t == "interrupt":
            yield self._emit("thinking.done")
            yield self._emit(
                "interrupt.required",
                content=event.get("message", ""),
                metadata={
                    "interrupt_id":   event.get("interrupt_id"),
                    "interrupt_type": event.get("interrupt_type"),
                    "message":        event.get("message"),
                    "metadata":       event.get("metadata", {}),
                },
            )

        elif t == "done":
            if self._token_buffer:
                full = "".join(self._token_buffer)
                self._token_buffer.clear()
                yield self._emit("message.ai.done", metadata={"full_content": full})
            yield self._emit("session.complete")

    def _enrich_progress(self, content: str) -> list[str]:
        """
        Map SuperAgent progress strings to structured event_classes.
        This is intentionally heuristic — see §14 for the SuperAgent
        changes that will make this deterministic.
        """
        lower = content.lower()
        if "calling" in lower or "invoking" in lower:
            # Extract tool name from "Calling fetch_emails..."
            parts = content.split()
            tool = parts[1].rstrip("...") if len(parts) > 1 else "tool"
            return [
                self._emit("invocation.start", content=content,
                           metadata={"tool_name": tool}),
                self._emit("thinking.step", content=content),
            ]
        if "checklist created" in lower:
            return [self._emit("checklist.created", content=content),
                    self._emit("thinking.step", content=content)]
        if "step" in lower and ("complete" in lower or "done" in lower):
            return [self._emit("checklist.updated", content=content),
                    self._emit("thinking.step", content=content)]
        if "discovering" in lower or "searching agents" in lower:
            return [self._emit("thinking.step", content=content)]
        # Default: generic thinking step
        return [self._emit("thinking.step", content=content)]
```

**Important:** The heuristic enrichment above is a bridge. Section 14 specifies the SuperAgent changes that replace heuristics with explicit structured event emission.

---

## 8. Session Stats Endpoints

These endpoints query the SuperAgent status endpoint and the Redis session index to return the structured data needed by the FE right panel.

```
GET /api/v1/sessions/:id/stats
  Auth:    required
  Returns: {
    session_id:       string
    status:           "active" | "interrupted" | "complete" | "error"
    estimated_tokens: int
    credits_usd:      float
    elapsed_seconds:  int           // now - created_at
    message_count:    int
    model:            string        // from SuperAgent config
    checklist:        ChecklistSnapshot | null
    agents:           AgentSnapshot[]
    artifacts:        ArtifactSnapshot[]
    pending_interrupt: InterruptSnapshot | null
  }

# Nested types:

ChecklistSnapshot:
  goal:  string
  steps: [ { step_id, description, status, result_summary? } ]

AgentSnapshot:
  agent_id:     string
  name:         string
  protocol:     "MCP" | "A2A" | "ACP"
  status:       "active" | "idle" | "error"
  call_count:   int

ArtifactSnapshot:
  artifact_id:  string
  description:  string
  mime_type:    string
  download_url: string    // gateway-proxied download URL

InterruptSnapshot:
  interrupt_id:   string
  interrupt_type: "auth" | "approval" | "clarify"
  message:        string
  elapsed_ms:     int
```

**Implementation:** Gateway calls `GET /sessions/:id/status` on SuperAgent (which reads from LangGraph's Redis checkpoint), maps the `AgentState` fields to the snapshot types above, and augments with session metadata from its own Redis store.

---

## 9. Credentials Routes

The Gateway proxies credential operations to SuperAgent's VaultService. It translates the FE-facing API (which talks about "session scope" vs "permanent") into the correct VaultService calls.

```
POST /api/v1/credentials
  Auth:    required
  Body:    {
    agent_id:  string
    credentials: { [var_name: string]: string }   // key → plaintext value
    scope: "session" | "permanent"
  }
  Action:
    - "permanent": POST /secrets/agent-env to SuperAgent (stores in Vault forever)
    - "session":   Store in Redis key credentials:{session_id}:{agent_id}:{var}
                   with TTL = session TTL. SuperAgent PreFlight will not find these
                   automatically — see §14.3 for session-scoped credential injection.
  Returns: 204

GET /api/v1/credentials/status/:session_id
  Auth:    required
  Query:   agent_id, var_names (comma-separated)
  Action:  Proxies GET /secrets/agent-env/:agent_id/status to SuperAgent
  Returns: {
    agent_id: string
    credentials: { [var_name]: "configured" | "missing" | "session_only" }
  }
  Note:    "session_only" = value is in GW Redis but not in Vault
```

---

## 10. Workflow Routes

```
POST /api/v1/workflows
  Auth:    required
  Body:    { session_id: string, name?: string }
  Action:  Calls GET /sessions/:id/status on SuperAgent,
           reads captured_workflow from state,
           persists to WorkflowTemplate table in Postgres with user_id
  Returns: { workflow_id, name, created_at }

GET /api/v1/workflows
  Auth:    required
  Query:   status? ("active"|"inactive"|"scheduled"), page?, limit?
  Returns: {
    workflows: [
      { workflow_id, name, status, last_run_at,
        next_run_at, trigger_type, step_count, agents_used[] }
    ],
    total: int
  }

GET /api/v1/workflows/:id
  Auth:    required (must own)
  Returns: full workflow detail including steps and execution log

PATCH /api/v1/workflows/:id
  Auth:    required (must own)
  Body:    { name?, schedule_cron?, schedule_enabled? }
  Returns: updated workflow record

DELETE /api/v1/workflows/:id
  Auth:    required (must own)
  Returns: 204

POST /api/v1/workflows/:id/run
  Auth:    required (must own)
  Action:  Creates a new session, injects workflow goal as first message
           Returns session_id so FE can open the SSE stream
  Returns: { session_id }
```

**Workflow Postgres model (additive to existing SuperAgent schema):**

```
model WorkflowTemplate {
  id               String    @id @default(uuid())
  user_id          String
  name             String
  goal_template    String
  steps            Json      // []{ description, agent_id? }
  agents_used      String[]
  parameters       Json      @default("{}")
  status           String    @default("inactive")  // "active"|"inactive"|"scheduled"
  schedule_cron    String?
  schedule_enabled Boolean   @default(false)
  next_run_at      DateTime?
  last_run_at      DateTime?
  run_count        Int       @default(0)
  created_at       DateTime  @default(now())
  updated_at       DateTime  @updatedAt

  @@index([user_id])
}
```

---

## 11. Agent Registration Routes (Dev Mode)

These proxy to the Registry service. All require `require_dev_mode` dependency.

```
GET /api/v1/dev/agents
  Auth:    dev mode required
  Returns: [ { agent_id, name, protocol, status, tags, registered_at } ]
  Action:  Proxies GET /api/v1/agents?developer_id={user_id} to Registry

POST /api/v1/dev/agents
  Auth:    dev mode required
  Body:    multipart/form-data: { manifest: File (.yaml) }
  Action:
    1. Parse YAML in Gateway (validate it's a valid emerge.yaml)
    2. POST parsed manifest JSON to Registry POST /api/v1/agents
    3. Tag agent with developer_id = user_id from JWT
  Returns: { agent_id, name, status: "pending_review" }
  Errors:  422 if YAML invalid

GET /api/v1/dev/agents/:id
  Auth:    dev mode required (must own agent)
  Action:  Proxies GET /api/v1/agents/:id to Registry
  Returns: full agent manifest + metrics stub

PATCH /api/v1/dev/agents/:id
  Auth:    dev mode required (must own agent)
  Body:    { name?, description?, tags?, status? }
  Action:  PATCH /api/v1/agents/:id on Registry
  Returns: updated agent record

DELETE /api/v1/dev/agents/:id
  Auth:    dev mode required (must own agent)
  Action:  DELETE /api/v1/agents/:id on Registry
  Returns: 204
```

---

## 12. Settings Routes

```
GET /api/v1/settings/profile
  Auth:    required
  Returns: { user_id, email, display_name, is_dev_mode, credits_usd, created_at }

PATCH /api/v1/settings/profile
  Auth:    required
  Body:    { display_name? }
  Returns: updated profile

PATCH /api/v1/settings/developer-mode
  Auth:    required
  Body:    { enabled: boolean }
  Action:  Updates User.is_dev_mode in Postgres
           Re-issues JWT with updated is_dev claim
  Returns: { access_token, refresh_token }   // FE replaces stored tokens

GET /api/v1/settings/credentials
  Auth:    required
  Returns: list of configured permanent credentials (agent_id + var_name only, NO values)

DELETE /api/v1/settings/credentials/:agent_id/:var_name
  Auth:    required
  Action:  Proxies delete to SuperAgent VaultService (add delete endpoint — see §14.2)
  Returns: 204
```

---

## 13. Health & Observability

```
GET /health
  Returns: {
    gateway:     "ok"
    superagent:  "ok" | "degraded" | "down"
    registry:    "ok" | "degraded" | "down"
    redis:       "ok" | "down"
    database:    "ok" | "down"
    version:     string
  }
  Note: Calls /health on each downstream. Uses 2s timeout.
        Returns 200 even if downstream degraded — caller checks fields.
        Returns 503 only if gateway itself is broken.

GET /metrics
  Returns: Prometheus text format
  Metrics:
    gateway_requests_total{method, path, status}
    gateway_sse_sessions_active
    gateway_sse_event_count{event_class}
    gateway_upstream_latency_seconds{service}
    gateway_auth_failures_total{reason}
```

---

## 14. Required Changes to SuperAgent Service

These are the changes needed in the SuperAgent codebase to support the Gateway contract properly. They are grouped by priority.

---

### 14.1 — CRITICAL: Enrich SSE events with structured typing

**Problem:** `runner.py::_extract_events()` only emits `token`, `progress`, `interrupt`, and `done`. The Gateway's SSERelay must heuristically parse `progress` strings to derive `invocation.start`, `checklist.updated` etc. This is fragile.

**Fix:** Extend `_extract_events()` to emit structured events for every significant state change. This is the **highest priority** change.

```python
# src/superagent/graph/runner.py — replace _extract_events()

def _extract_events(chunk: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract ALL streamable events from a LangGraph graph chunk.
    Each event has a 'type' field that the Gateway maps directly
    to a GatewaySSEEvent event_class.
    """
    events: list[dict[str, Any]] = []
    messages = chunk.get("messages", [])

    if messages:
        last = messages[-1]
        content = getattr(last, "content", "")
        msg_type = type(last).__name__

        if msg_type == "AIMessage":
            tool_calls = getattr(last, "tool_calls", [])
            if tool_calls:
                # LLM decided to call tools — emit invocation.start for each
                for tc in tool_calls:
                    events.append({
                        "type": "invocation_start",
                        "tool_name": tc.get("name", ""),
                        "call_id": tc.get("id", ""),
                        "args_preview": _preview(tc.get("args", {})),
                    })
            elif isinstance(content, str) and content:
                events.append({"type": "token", "content": content})

        elif msg_type == "ToolMessage":
            # Tool result returned
            events.append({
                "type": "invocation_result",
                "tool_call_id": getattr(last, "tool_call_id", ""),
                "content_preview": str(content)[:300],
                "full_content": content,
            })

        elif msg_type == "HumanMessage":
            pass  # human messages are echoed by GW, not SA

    # Checklist state change
    checklist = chunk.get("task_checklist")
    if checklist is not None:
        events.append({
            "type": "checklist_snapshot",
            "goal": getattr(checklist, "goal", ""),
            "steps": [
                {
                    "step_id":      getattr(s, "step_id", ""),
                    "description":  getattr(s, "description", ""),
                    "status":       getattr(s, "status", "pending"),
                    "result_summary": getattr(s, "result_summary", ""),
                }
                for s in getattr(checklist, "steps", [])
            ],
        })

    # PnD candidates (agents discovered this turn)
    pnd_candidates = chunk.get("pnd_candidates", [])
    if pnd_candidates:
        events.append({
            "type": "agents_discovered",
            "agents": [
                {
                    "agent_id":     getattr(c, "agent_id", ""),
                    "name":         getattr(c, "name", ""),
                    "protocol":     getattr(c, "protocol_type", ""),
                    "capabilities": [
                        getattr(cap, "capability_id", "")
                        for cap in getattr(c, "capabilities", [])
                    ],
                }
                for c in pnd_candidates
            ],
        })

    # Token usage
    token_count = chunk.get("estimated_token_count")
    if token_count:
        events.append({
            "type": "token_usage",
            "estimated_tokens": token_count,
        })

    # Artifacts
    artifacts = chunk.get("artifacts", {})
    if artifacts:
        for artifact_id, ref in artifacts.items():
            events.append({
                "type": "artifact_created",
                "artifact_id": artifact_id,
                "mime_type":   getattr(ref, "mime_type", ""),
                "description": getattr(ref, "description", ""),
                "storage_key": getattr(ref, "storage_key", ""),
            })

    # Interrupt
    interrupt = chunk.get("pending_interrupt")
    if interrupt:
        events.append({
            "type": "interrupt",
            "interrupt_id":   getattr(interrupt, "interrupt_id", ""),
            "interrupt_type": getattr(interrupt, "interrupt_type", "unknown"),
            "message":        getattr(interrupt, "message", ""),
            "agent_id":       getattr(interrupt, "agent_id", None),
            "metadata":       getattr(interrupt, "metadata", {}),
        })

    return events


def _preview(obj: Any, max_len: int = 120) -> str:
    s = json.dumps(obj) if not isinstance(obj, str) else obj
    return s[:max_len] + "..." if len(s) > max_len else s
```

This change also removes all heuristic parsing from `SSERelay._enrich_progress()` — the Gateway simply maps SuperAgent's structured `type` values directly to `event_class` values via a lookup table.

---

### 14.2 — HIGH: Add credential delete endpoint to VaultService

**Problem:** Settings screen needs to let users delete stored credentials. No delete exists.

**Add to `src/superagent/api/routes.py`:**

```python
@router.delete("/secrets/agent-env/{agent_id}/{var_name}", status_code=204)
async def delete_agent_env(
    agent_id: str,
    var_name: str,
    user_id: str,               # query param
) -> None:
    """Delete a stored agent env credential from the vault."""
    from ..vault.client import VaultClient
    vault = VaultClient()
    await vault.delete_agent_env(user_id, agent_id, var_name)
```

**Add to `VaultClient`:**

```python
async def delete_agent_env(self, user_id: str, agent_id: str, var_name: str) -> None:
    key = f"agent:{agent_id}:env:{var_name}"
    from src.generated_client import Prisma
    db = Prisma()
    await db.connect()
    try:
        await db.usersecret.delete(
            where={"user_id_key": {"user_id": user_id, "key": key}}
        )
    except Exception:
        pass   # ignore not-found
    finally:
        await db.disconnect()
```

---

### 14.3 — HIGH: Session-scoped credential injection

**Problem:** When users store credentials with `scope: "session"`, the Gateway holds them in Redis but SuperAgent's `PreFlightManager` only reads from the Vault (Postgres). Session-scoped credentials never reach the agent.

**Fix:** Add an optional `session_credentials` field to the SuperAgent message request. The Gateway injects session-scoped credentials from Redis into each message body.

**In `src/superagent/api/models.py` — extend `MessageRequest`:**

```python
class MessageRequest(BaseModel):
    user_id: str
    message: str
    # Gateway injects session-scoped credentials here (never stored in Vault)
    session_credentials: dict[str, dict[str, str]] = {}
    # Structure: { agent_id: { VAR_NAME: plaintext_value } }
```

**In `src/superagent/middleware/preflight.py` — consume injected credentials:**

```python
# In PreFlightManager._resolve_stdio_env(), before vault lookup:
session_creds = self._state.get("session_credentials", {})
agent_creds = session_creds.get(agent_id, {})
if var_name in agent_creds:
    resolved[var_name] = agent_creds[var_name]
    continue  # skip vault lookup
```

**In `src/superagent/graph/runner.py` — store in state:**

```python
# In run_turn(), when building state_update:
if body.session_credentials:
    state_update["session_credentials"] = body.session_credentials
```

**Add `session_credentials` to `AgentState`:**

```python
session_credentials: dict[str, dict[str, str]]  # injected per-message, not persisted
```

---

### 14.4 — MEDIUM: Expose `get_status` full state snapshot

**Problem:** `GET /sessions/:id/status` currently returns only `{ status, pending_interrupt, session_id }`. The Gateway stats endpoint needs `estimated_token_count`, `artifacts`, `pnd_candidates`, `task_checklist`, and `captured_workflow`.

**Fix:** Extend `SessionRunner.get_status()` to return the full relevant state slice:

```python
async def get_status(self, session_id: str, ...) -> dict[str, Any]:
    config = thread_config or {"configurable": {"thread_id": session_id}}
    snapshot = await self._graph.aget_state(config)
    if not snapshot or not snapshot.values:
        return {"status": "not_found"}

    state = snapshot.values
    pending = state.get("pending_interrupt")
    checklist = state.get("task_checklist")
    artifacts = state.get("artifacts", {})
    pnd_candidates = state.get("pnd_candidates", [])

    return {
        "status": "interrupted" if pending else "ready",
        "session_id": session_id,
        "estimated_token_count": state.get("estimated_token_count", 0),
        "pending_interrupt": _serialise_interrupt(pending),
        "task_checklist": _serialise_checklist(checklist),
        "artifacts": _serialise_artifacts(artifacts),
        "agents": _serialise_candidates(pnd_candidates),
        "captured_workflow": _serialise_workflow(state.get("captured_workflow")),
    }
```

Add the `_serialise_*` helpers as simple dataclass-to-dict converters.

---

### 14.5 — LOW: `progress` events from system tools

System tools (checklist, artifacts, workflow) currently mutate state silently. They should emit `progress` events so the SSE stream reflects in-progress work before the state chunk arrives.

**Pattern to add to each system tool handler:**

```python
# In _create_checklist, after constructing checklist object:
state.setdefault("_progress_events", []).append({
    "type": "progress",
    "content": f"Checklist created: {goal}",
    "subtype": "checklist_created",
})
```

The runner's `_extract_events` reads and clears `_progress_events` from each chunk, emitting them before other events.

---

## 15. Error Handling Contract

All Gateway error responses follow this envelope:

```json
{
  "error": {
    "code":    "SESSION_NOT_FOUND",
    "message": "Session abc123 does not exist or you do not have access.",
    "detail":  {}
  }
}
```

Standard error codes:

| HTTP | Code | Trigger |
|------|------|---------|
| 400 | `INVALID_REQUEST` | Body validation failed |
| 401 | `AUTH_REQUIRED` | Missing/invalid JWT |
| 401 | `TOKEN_EXPIRED` | JWT expired |
| 401 | `TOKEN_REVOKED` | Logged out token |
| 403 | `DEV_MODE_REQUIRED` | Accessing dev endpoint without dev mode |
| 403 | `SESSION_NOT_OWNED` | Accessing another user's session |
| 404 | `SESSION_NOT_FOUND` | Session doesn't exist |
| 404 | `WORKFLOW_NOT_FOUND` | Workflow doesn't exist |
| 409 | `EMAIL_TAKEN` | Registration with existing email |
| 422 | `INVALID_MANIFEST` | Bad emerge.yaml during agent registration |
| 429 | `RATE_LIMITED` | Per-user rate limit exceeded |
| 502 | `UPSTREAM_ERROR` | SuperAgent/Registry returned error |
| 503 | `UPSTREAM_UNAVAILABLE` | SuperAgent/Registry unreachable |

SSE error (mid-stream):

```json
{
  "event_class": "session.error",
  "session_id": "...",
  "seq": 14,
  "ts": "...",
  "content": "Upstream SuperAgent became unavailable",
  "metadata": { "code": "UPSTREAM_UNAVAILABLE" }
}
```

---

## 16. Rate Limiting

Implemented via Redis sliding window counters, applied per `user_id` (not per IP).

```
Default routes:           60 req/min
POST .../message:         20 req/min
POST .../resume:          20 req/min
POST /auth/login:         10 req/min  (per IP, brute-force protection)
POST /auth/register:      5 req/min   (per IP)
POST /dev/agents:         10 req/min
```

`429` response includes `Retry-After` header.

---

## 17. pyproject.toml

```toml
[project]
name = "gateway"
version = "0.1.0"
description = "MetaOrcha Gateway Service"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.115",
  "uvicorn[standard]>=0.29",
  "pydantic>=2",
  "pydantic-settings>=2",
  "python-jose[cryptography]>=3.3",
  "passlib[bcrypt]>=1.7",
  "httpx[http2]>=0.27",
  "httpx-sse>=0.4",
  "redis>=5",
  "asyncpg>=0.29",
  "prisma>=0.15",
  "python-multipart>=0.0.9",   # for YAML file upload
  "pyyaml>=6",                  # emerge.yaml parsing
  "common-database",
]

[tool.uv.sources]
common-database = {workspace = true}
```

---

## 18. Summary of SuperAgent Changes

| # | File | Change | Priority |
|---|------|--------|----------|
| 14.1 | `graph/runner.py` | Replace `_extract_events()` with structured multi-type emitter | **CRITICAL** |
| 14.2 | `api/routes.py` + `vault/client.py` | Add `DELETE /secrets/agent-env/:agent_id/:var_name` | HIGH |
| 14.3 | `api/models.py` + `middleware/preflight.py` + `graph/runner.py` + `graph/state.py` | Session-scoped credential injection via `session_credentials` field | HIGH |
| 14.4 | `graph/runner.py` | Extend `get_status()` to return full state snapshot | MEDIUM |
| 14.5 | `system_tools/*.py` | Emit `_progress_events` from system tool handlers | LOW |


## Q1 — Do GW and SuperAgent share the same Redis cluster?

**Answer: No. They should use separate logical databases on the same Redis instance (or separate clusters in production), with clearly separated key namespaces and ownership.**

Here's the breakdown:

### What SuperAgent uses Redis for
SuperAgent uses Redis exclusively via **LangGraph's `RedisSaver` checkpointer**. This stores the full serialised `AgentState` (messages, checklist, artifacts, pnd_candidates, etc.) keyed by LangGraph's internal `thread_id` (which equals `session_id`).

Key pattern (LangGraph-managed, not yours):
```
langgraph:checkpoint:{thread_id}:*
langgraph:writes:{thread_id}:*
```

This is **LangGraph's private storage**. You do not read or write these keys directly — you go through `graph.aget_state()`.

### What Gateway uses Redis for
The Gateway needs Redis for:
```
session:{session_id}              → session index hash (user_id, title, status, etc.)
sessions:user:{user_id}           → sorted set of session_ids by created_at
revoked_tokens                    → set of revoked JWT jti values
ratelimit:{user_id}:{route}       → sliding window counters
credentials:session:{session_id}:{agent_id}:{var_name}  → session-scoped creds
```

These are **Gateway-owned keys** with no overlap with LangGraph's keyspace.

### Decision: Separate DB indexes on same instance (dev), separate clusters (prod)

```
Dev:
  Redis DB 0  →  SuperAgent (LangGraph checkpointer)
  Redis DB 1  →  Gateway (session index, auth, rate-limit, session-creds)

Prod:
  redis-superagent.internal:6379  →  SuperAgent only
  redis-gateway.internal:6379     →  Gateway only
```

**Why separate even in dev?** LangGraph's checkpointer does `FLUSHDB` in some test scenarios. You don't want that wiping your session index or rate-limit counters. Namespace isolation prevents accidental cross-contamination and makes each service independently scalable.

### Config changes

```python
# src/gateway/config.py
class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379/1"   # DB 1, not DB 0
    # ...

# superagent/.env
REDIS_URL=redis://localhost:6379/0   # DB 0 for LangGraph
```

```python
# src/gateway/main.py — lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = await aioredis.from_url(
        settings.redis_url,      # redis://…/1
        decode_responses=True,
        socket_timeout=5,
    )
    yield
    await app.state.redis.aclose()
```

---

## Q2 — How does SuperAgent track which task is being done by which agent/tool?

**Current state: it doesn't — and this is a gap.**

Reading the code precisely:

- `task_checklist` (`ChecklistStep`) has `step_id`, `description`, `status`, `result_summary` — but **no `agent_id` or `tool_name` field**.
- `execute_agent_calls_node` runs tool calls but only writes back to `task_checklist` via `_auto_update_checklist()`, which does a loose string match (`if agent_id in tool_name`) — not a reliable binding.
- `invocation_start` / `invocation_result` events (from the spec change in §14.1) carry `tool_name` and `call_id` but are not linked to a `step_id`.
- The FE has no way to draw an arrow from "fetch_emails agent" → "Step 2: Fetch emails".

### The fix: Two-part change across SuperAgent

---

### Part A — Add `agent_id` + `tool_name` to `ChecklistStep`

```python
# src/superagent/graph/state.py

@dataclass
class ChecklistStep:
    step_id:        str
    description:    str
    status:         str = "pending"   # pending|in_progress|done|failed
    result_summary: str = ""
    # ── NEW FIELDS ──────────────────────────────────────────────────
    agent_id:       str | None = None  # DID of the agent assigned to this step
    tool_name:      str | None = None  # exact tool name called (agent_id__capability_id)
    call_id:        str | None = None  # LLM tool_call id — links to invocation events
    started_at:     str | None = None  # ISO timestamp when step went in_progress
    completed_at:   str | None = None  # ISO timestamp when step went done/failed
```

---

### Part B — Bind the step to the tool call at dispatch time

The binding happens in two places in `execute_agent_calls_node`:

**1. Before dispatch — mark step `in_progress` and stamp identifiers:**

```python
# src/superagent/nodes/execute_agent_calls.py
# Inside the for tc in tool_calls loop, BEFORE middleware.execute():

from datetime import UTC, datetime

tool_name: str = tc.get("name", "")
call_id:   str = tc.get("id", "")

# Bind this tool call to a checklist step
_bind_step_to_call(state, tool_name, call_id, agent_id)
```

```python
def _bind_step_to_call(
    state: dict,
    tool_name: str,
    call_id: str,
    agent_id: str,
) -> None:
    """
    Find the best-matching pending checklist step for this tool call
    and stamp it with agent_id, tool_name, call_id, and started_at.

    Matching strategy (in order):
      1. Exact step.agent_id == agent_id  (if the LLM already set it)
      2. step.tool_name == tool_name      (previously bound in prior turn)
      3. First pending step with no binding yet (greedy first-fit)
    """
    checklist = state.get("task_checklist")
    if checklist is None:
        return

    now = datetime.now(UTC).isoformat()

    for step in checklist.steps:
        if step.status not in ("pending", "in_progress"):
            continue
        match = (
            (step.agent_id is not None and step.agent_id == agent_id)
            or (step.tool_name is not None and step.tool_name == tool_name)
            or (step.agent_id is None and step.tool_name is None)  # unbound, claim it
        )
        if match:
            step.agent_id   = agent_id
            step.tool_name  = tool_name
            step.call_id    = call_id
            step.status     = "in_progress"
            step.started_at = now
            break
```

**2. After dispatch — mark step `done`/`failed` and stamp `completed_at`:**

```python
# Replace the existing _auto_update_checklist() in pipeline.py:

def _auto_update_checklist(
    self,
    tool_name: str,
    call_id: str,
    result_summary: str,
    success: bool,
) -> None:
    checklist = self._state.get("task_checklist")
    if not checklist:
        return
    now = datetime.now(UTC).isoformat()
    for step in checklist.steps:
        # Primary match: exact call_id (most reliable)
        # Fallback: tool_name match (for cases where call_id wasn't stamped)
        if step.call_id == call_id or (
            step.call_id is None and step.tool_name == tool_name
        ):
            step.status       = "done" if success else "failed"
            step.result_summary = result_summary[:200]
            step.completed_at   = now
            break
```

Update the call site in `pipeline.py`:
```python
# Step 7: Checklist auto-update — pass call_id through
self._auto_update_checklist(
    tool_name,
    call_id,       # ← add this
    normalised.get("content", ""),
    success=True,
)
```

---

### Part C — Emit the binding in the SSE stream

With the `_extract_events` changes from §14.1, the `checklist_snapshot` event now includes `agent_id`, `tool_name`, `call_id` on each step. The Gateway maps this directly into `checklist.updated` events on the SSE stream:

```python
# Updated checklist_snapshot emission in _extract_events():

{
    "type": "checklist_snapshot",
    "goal": checklist.goal,
    "steps": [
        {
            "step_id":       step.step_id,
            "description":   step.description,
            "status":        step.status,
            "agent_id":      step.agent_id,      # ← now included
            "tool_name":     step.tool_name,     # ← now included
            "call_id":       step.call_id,       # ← now included
            "result_summary": step.result_summary,
            "started_at":    step.started_at,
            "completed_at":  step.completed_at,
        }
        for step in checklist.steps
    ],
}
```

---

### How the FE renders it

With these changes the FE receives events in this sequence for every tool call:

```
1. checklist.created        → steps rendered as ○ pending, no agent assigned yet

2. checklist.updated        → step N flips to ◐ in_progress
                               metadata.agent_id = "did:orcha:agent:gmail-mcp"
                               metadata.tool_name = "gmail-mcp__bulk_fetch_emails"
                               metadata.call_id = "call_abc123"

3. invocation.start         → metadata.call_id = "call_abc123"  ← same call_id
                               metadata.tool_name = "gmail-mcp__bulk_fetch_emails"
                               metadata.agent_id = "did:orcha:agent:gmail-mcp"
   → FE joins on call_id: the invocation card in "Logs" panel highlights
     the corresponding task row in "Checklist" panel

4. invocation.result        → metadata.call_id = "call_abc123"
                               metadata.result_preview = "Fetched 47 emails..."

5. checklist.updated        → step N flips to ✓ done
                               metadata.call_id = "call_abc123"
                               metadata.completed_at = "2026-04-01T..."
```

The `call_id` is the **join key** across all three FE panels — Agents, Checklist, and Logs — giving you a fully traceable execution graph in the UI without any guessing.

---

## Summary

| Question | Answer |
|---|---|
| Shared Redis? | No — DB 0 for SuperAgent/LangGraph, DB 1 for Gateway. Separate clusters in prod. |
| Agent→task mapping today | Broken — loose string match in `_auto_update_checklist`, no `call_id` binding |
| Fix location | `ChecklistStep` dataclass (add 4 fields) + `_bind_step_to_call()` before dispatch + `_auto_update_checklist()` uses `call_id` after dispatch |
| FE join key | `call_id` — emitted on `checklist.updated`, `invocation.start`, and `invocation.result` — FE correlates all three panels on this single field |