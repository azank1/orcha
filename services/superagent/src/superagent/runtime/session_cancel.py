"""Cooperative kill-switch for in-flight graph work.

Task.cancel() alone does not reliably stop LangGraph node bodies that await long
LLM streams or agent I/O. We pair it with a per-session ``asyncio.Event`` that
orchestrator streaming and tool execution consult so stop takes effect quickly.
"""

from __future__ import annotations

import asyncio
import logging
logger = logging.getLogger(__name__)

_lock = asyncio.Lock()
_events: dict[str, asyncio.Event] = {}


async def register_run(session_id: str) -> None:
    """Begin a graph run for ``session_id`` with a fresh (unset) cancel flag."""
    async with _lock:
        _events[session_id] = asyncio.Event()


async def unregister_run(session_id: str) -> None:
    """Clear bookkeeping after a run finishes or errors."""
    async with _lock:
        _events.pop(session_id, None)


def get_cancel_event(session_id: str) -> asyncio.Event | None:
    """Return the live cancel event for this session, if any."""
    return _events.get(session_id)


def signal_cancel(session_id: str) -> None:
    """Set the cancel flag (idempotent). Called from POST /sessions/{id}/stop."""
    ev = _events.get(session_id)
    if ev is not None:
        ev.set()
        logger.info("session_cancel: flag set session_id=%s", session_id)


def is_cancelled(session_id: str) -> bool:
    ev = _events.get(session_id)
    return ev is not None and ev.is_set()


def session_id_from_config(config: object | None) -> str | None:
    """LangGraph thread_id is the conversation session id."""
    if not config:
        return None
    conf = config.get("configurable") if isinstance(config, dict) else None
    if not isinstance(conf, dict):
        return None
    tid = conf.get("thread_id")
    return str(tid) if tid else None
