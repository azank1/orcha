"""PnD gate — decides whether to call Planning & Discovery for agent candidates.

Tier 1a — Active checklist → always True (incomplete work needs tools)
Tier 1b — NO_TOOL regex match, no TOOL regex match → False (fast skip)
Tier 1c — TOOL regex match → True (fast pass)
Tier 2  — Cosine similarity to tool-anchor embeddings (all-MiniLM-L6-v2)
           >0.6 → True, <0.3 → False, 0.3-0.6 → Tier 3
Tier 3  — Haiku YES/NO classifier

Call warm_up_gate_encoder() at service startup so Tier 2 never cold-starts
during a live request (the 80 MB model load is ~2-5 s on first use).
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# ── Tier-1 regex patterns ──────────────────────────────────────────────────────

_NO_TOOL_RE = re.compile(
    r"\b(hello|hi|hey|thanks|thank you|bye|goodbye|what is|who is|define|explain"
    r"|tell me about|how does|why does|what are|what does|how do I write|help me understand"
    r"|what.?s the (difference|meaning|definition)|yes|no|ok|okay|sure)\b",
    re.IGNORECASE,
)

_TOOL_RE = re.compile(
    r"\b(send|fetch|get|retrieve|create|delete|update|list|search|find|email|calendar"
    r"|schedule|book|order|buy|pay|upload|download|read|write|edit|file|document"
    r"|message|call|run|execute|check|monitor|deploy|build|compile|test|analyse|analyze"
    r"|generate|summarise|summarize|translate|convert|scrape|crawl|browse|visit|pull"
    r"|https?://)\b",
    re.IGNORECASE,
)

# ── Tier-2 anchor phrases (embedded once at import) ───────────────────────────

_TOOL_ANCHORS = [
    "fetch my emails",
    "book a meeting",
    "search the web",
    "create a document",
    "send a message",
    "run a script",
    "deploy the service",
    "check the weather",
    "order food",
    "read a file",
    "scrape this website",
    "get the contents of a web page",
    "read a github repository",
]

_encoder: Any = None  # lazy-loaded sentence-transformers model
_anchor_vecs: Any = None  # ndarray (N, D)


def _load_encoder() -> Any:
    """Blocking load — call only from a thread executor."""
    global _encoder, _anchor_vecs
    if _encoder is None:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading all-MiniLM-L6-v2 for PnD gate (one-time ~80 MB)…")
        _encoder = SentenceTransformer("all-MiniLM-L6-v2")
        _anchor_vecs = _encoder.encode(_TOOL_ANCHORS, normalize_embeddings=True)
        logger.info("all-MiniLM-L6-v2 loaded")
    return _encoder


def _get_encoder() -> Any:
    return _load_encoder()


def warm_up_gate_encoder() -> None:
    """Pre-load the sentence-transformers model synchronously (call from startup thread)."""
    _load_encoder()


def _cosine_sim(a: Any, b: Any) -> float:
    return float(np.dot(a, b.T).max())


def _encode_sync(text: str) -> Any:
    enc = _get_encoder()
    return enc.encode([text], normalize_embeddings=True)[0]


# ── Public gate function ───────────────────────────────────────────────────────


async def pnd_gate(
    state: dict[str, Any],
    small_llm: AsyncOpenAI,
    small_model: str,
) -> bool:
    """
    Return True if the orchestrator should call PnD for agent candidates.

    Args:
        state:      Current AgentState dict.
        small_llm:  Async OpenAI client pointed at OpenRouter.
        small_model: Model ID for Tier-3 fast classifier (OpenRouter, e.g. anthropic/claude-sonnet-4).
    """
    # Tier 1a — active checklist with incomplete steps
    checklist = state.get("task_checklist")
    if checklist is not None:
        steps = getattr(checklist, "steps", [])
        if any(getattr(s, "status", "") in ("pending", "in_progress") for s in steps):
            logger.info("pnd_gate=True reason=tier1a_active_checklist")
            return True

    messages = state.get("messages", [])
    if not messages:
        return False
    last_content = getattr(messages[-1], "content", "") or ""
    if not isinstance(last_content, str):
        last_content = str(last_content)

    # Tier 1b — pure conversational (NO_TOOL hit and no action / URL signal)
    if _NO_TOOL_RE.search(last_content) and not _TOOL_RE.search(last_content):
        logger.info(
            "pnd_gate=False reason=tier1b_no_tool_pattern query_preview=%.120s",
            last_content.replace("\n", " "),
        )
        return False

    # Tier 1c — explicit action verb or URL
    if _TOOL_RE.search(last_content):
        logger.info(
            "pnd_gate=True reason=tier1c_tool_or_url_pattern query_preview=%.120s",
            last_content.replace("\n", " "),
        )
        return True

    # Tier 2 — embedding cosine similarity (offloaded to thread to avoid blocking event loop)
    try:
        loop = asyncio.get_event_loop()
        query_vec = await loop.run_in_executor(None, _encode_sync, last_content)
        sim = _cosine_sim(query_vec, _anchor_vecs)
        logger.debug("PnD gate Tier2: cosine_sim=%.3f", sim)
        if sim > 0.6:
            logger.info(
                "pnd_gate=True reason=tier2_embedding_sim=%.3f query_preview=%.120s",
                sim,
                last_content.replace("\n", " "),
            )
            return True
    except Exception:
        logger.exception("PnD gate Tier2 embedding failed — falling through to Tier3")

    # Tier 3 — small LLM YES/NO
    try:
        resp = await small_llm.chat.completions.create(
            model=small_model,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Does this user message require calling an external tool "
                        f"or agent? Reply YES or NO only.\n\nMessage: {last_content}"
                    ),
                }
            ],
            max_tokens=5,
            temperature=0,
        )
        answer = (resp.choices[0].message.content or "").strip().upper()
        decided = answer.startswith("Y")
        logger.info(
            "pnd_gate=%s reason=tier3_haiku answer=%r query_preview=%.120s",
            decided,
            answer,
            last_content.replace("\n", " "),
        )
        return decided
    except Exception:
        logger.exception("PnD gate Tier3 LLM call failed — defaulting True")
        return True
