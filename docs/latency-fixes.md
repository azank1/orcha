# Latency Fixes — SuperAgent / Planning-Discovery Stack

## Problem

End-to-end latency for a typical lead-gen run was 60–120 s, split across five
identifiable bottlenecks.  The OpenRouter model was not the cause — the delays
were entirely in infrastructure and polling code.

---

## Root Causes & Fixes

### Fix 1 — A2A poll interval: 2 s fixed → exponential backoff (0.1 s → 1 s)

**File:** `services/superagent/src/superagent/handlers/a2a_handler.py`

**Before:**
```python
_POLL_INTERVAL = 2.0  # seconds
_MAX_POLLS = 60

for _ in range(_MAX_POLLS):
    await asyncio.sleep(_POLL_INTERVAL)
```

**After:**
```python
_POLL_INITIAL = 0.1   # first check after 100 ms
_POLL_MAX = 1.0       # cap per interval
_MAX_POLLS = 120      # keeps the same ~2 min total budget

_interval = _POLL_INITIAL
for _ in range(_MAX_POLLS):
    await asyncio.sleep(_interval)
    _interval = min(_interval * 2, _POLL_MAX)
```

**Impact:** The first status check now fires after 100 ms instead of 2 s.
For a lead-gen run that finishes in 30 s, this shaves ~1.9 s off the minimum
overhead and reduces cumulative polling waste from ~60 s to ~30 s budget.

---

### Fix 2 — Skip PnD re-discovery on tool-result turns

**File:** `services/superagent/src/superagent/nodes/orchestrator.py`

**Problem:** `orchestrator_llm_node` is called on every LangGraph turn —
including after every tool result.  Each call unconditionally ran the 3-tier
PnD gate and, when it fired (which it always did for lead-gen queries containing
action verbs), issued a full hybrid search request to the Planning & Discovery
service (~300–500 ms per call × N turns).

A typical 5-step lead-gen run generates 10+ orchestrator turns, meaning 10+
PnD calls for the same agent.

**Fix:** When the last message in state is a `ToolMessage` (i.e. we are
processing a tool result, not a fresh user query), reuse the `pnd_candidates`
already stored in LangGraph state and reconstruct the tool schemas locally.

```python
last_is_tool_result = messages and isinstance(messages[-1], ToolMessage)

if last_is_tool_result and cached_candidates:
    # Fast path: zero network calls — rebuild schemas from state
    pnd_candidates = cached_candidates
    pnd_tools = _candidates_to_tools(cached_candidates)
else:
    needs_external = await pnd_gate(...)
    # ... normal PnD fetch
```

`_candidates_to_tools()` is a local helper that reconstructs OpenAI function
schemas from the serialised candidate dicts already in state — no HTTP call
required.

**Impact:** Eliminates N-1 PnD round-trips per session (only the first turn
and genuine new-user-query turns incur a PnD call).

---

### Fix 3 — Singleton LLM clients (avoid TCP reconnect per turn)

**File:** `services/superagent/src/superagent/nodes/orchestrator.py`

**Before:** `orchestrator_llm_node` constructed a fresh `AsyncOpenAI` and
`ChatOpenAI` instance on every invocation:
```python
small_llm = AsyncOpenAI(api_key=..., base_url=...)   # new TCP connection
chat = ChatOpenAI(model=..., streaming=True, ...)     # new TCP connection
```

**After:** Both clients are module-level singletons, lazily initialised once:
```python
_small_llm: AsyncOpenAI | None = None
_chat_llm: ChatOpenAI | None = None

def _get_small_llm() -> AsyncOpenAI: ...   # init once, reuse forever
def _get_chat_llm() -> ChatOpenAI: ...
```

**Impact:** Eliminates TCP handshake overhead on every turn.  HTTP/2
multiplexing and keep-alive connections to OpenRouter are maintained across
turns.

---

### Fix 4 — Warm up PnD gate encoder at startup

**Files:**
- `services/superagent/src/superagent/pnd/gate.py`
- `services/superagent/src/superagent/main.py`

**Problem:** The `all-MiniLM-L6-v2` sentence-transformers model used by PnD
gate Tier 2 was lazy-loaded on the first request.  Loading ~80 MB from disk
takes 2–5 s and was previously done synchronously inside an async function,
blocking the event loop.

**Fix 1 — warm at startup:**
```python
# main.py lifespan
loop.run_in_executor(None, warm_up_gate_encoder)
```

`warm_up_gate_encoder()` is a new function in `gate.py` that calls
`_load_encoder()` from a background thread during app startup, so the model
is already in memory by the time the first user request arrives.

**Fix 2 — offload encode to thread:**
```python
# gate.py Tier 2
loop = asyncio.get_event_loop()
query_vec = await loop.run_in_executor(None, _encode_sync, last_content)
```

The `enc.encode()` call is CPU-bound and was previously blocking the async
event loop.  It is now offloaded to the default thread pool executor.

**Impact:** Eliminates 2–5 s cold-start delay on first request; prevents
event loop stalls on every Tier-2 evaluation thereafter.

---

### Fix 5 — Embedding LRU cache in hybrid search

**File:** `services/planning-discovery/src/planning_discovery/planning/resolution/hybrid_search.py`

**Problem:** Every call to `_vector_search()` inside the PnD candidates
endpoint issued a remote embedding API call, even when the exact same
query had been seen moments before (common when the orchestrator re-queries
PnD with identical or near-identical context strings).

**Fix:** A 128-entry process-level insertion-order eviction cache:
```python
_embed_cache: dict[tuple[str, str], list[float]] = {}

async def _embed_cached(self, query: str) -> list[float]:
    cached = _embed_cache_get(query, self._embedding_model)
    if cached is not None:
        return cached          # ~0 ms
    result = await self._llm.embed(query, self._embedding_model)
    _embed_cache_set(query, self._embedding_model, result)
    return result
```

**Impact:** Cache hit = ~0 ms vs ~200–400 ms remote embedding call.  Hits
on repeated or context-extended queries during multi-turn sessions.

---

## Summary of Expected Gains

| Fix | Before | After | Saving |
|-----|--------|-------|--------|
| A2A poll first check | 2 000 ms | 100 ms | ~1 900 ms |
| A2A poll per interval | 2 000 ms | ≤1 000 ms avg | ~50% |
| PnD call per tool-result turn | ~400 ms × N | 0 ms | ~2–4 s per run |
| TCP reconnect per turn | ~50 ms × N | ~0 ms | ~0.5 s per run |
| Gate encoder cold start | 2 000–5 000 ms | 0 ms (warmed) | one-time |
| Embedding repeat call | ~300 ms | ~0 ms (cache) | per cache hit |

For a typical 5-step lead-gen run, total expected reduction: **15–25 s**.

---

## Files Changed

| File | Change |
|------|--------|
| `services/superagent/src/superagent/handlers/a2a_handler.py` | Exponential backoff poll |
| `services/superagent/src/superagent/nodes/orchestrator.py` | Singleton clients + ToolMessage shortcut |
| `services/superagent/src/superagent/pnd/gate.py` | Warm-up function + executor offload |
| `services/superagent/src/superagent/main.py` | Startup warm-up call |
| `services/planning-discovery/src/planning_discovery/planning/resolution/hybrid_search.py` | Embedding LRU cache |

## Restart Required

Both services must be restarted to pick up all changes:

```bash
# from repo root
make restart-superagent
make restart-planning-discovery
# or
docker compose -f docker-compose.local.yml restart superagent planning-discovery
```
