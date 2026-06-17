"""SandboxGuard — lightweight request guard for the hosted sandbox.

Active only when SANDBOX_MODE=true. Enforces two limits via Redis:

1. Daily message cap (SANDBOX_MAX_DAILY_MESSAGES, default 500)
   Counts POST requests to /api/v1/sessions/*/message per UTC day.
   Returns 429 when exceeded so the sandbox doesn't run up an open tab.

2. Per-IP rate: handled upstream by nginx (10 req/min). This guard is
   belt-and-suspenders at the app layer.

Usage: mounted as ASGI middleware in main.py when SANDBOX_MODE=true.
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

_MAX_DAILY = int(os.getenv("SANDBOX_MAX_DAILY_MESSAGES", "500"))

_CAP_BODY = {
    "detail": "Sandbox daily limit reached. The demo resets at midnight UTC. "
    "Run locally for unlimited access: https://github.com/azank1/orcha",
    "code": "SANDBOX_DAILY_LIMIT",
}


def _is_message_request(path: str, method: str) -> bool:
    """True for POST /api/v1/sessions/<id>/message."""
    if method != "POST":
        return False
    parts = path.strip("/").split("/")
    # api / v1 / sessions / <id> / message
    return (
        len(parts) == 5
        and parts[0] == "api"
        and parts[1] == "v1"
        and parts[2] == "sessions"
        and parts[4] == "message"
    )


class SandboxGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        if not _is_message_request(request.url.path, request.method):
            return await call_next(request)

        redis = getattr(request.app.state, "redis", None)
        if redis is None:
            return await call_next(request)

        today = datetime.now(UTC).strftime("%Y-%m-%d")
        key = f"sandbox:messages:{today}"

        try:
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, 90000)  # 25h — covers DST edge
            if count > _MAX_DAILY:
                logger.warning("Sandbox daily message cap reached: %d/%d", count, _MAX_DAILY)
                return JSONResponse(status_code=429, content=_CAP_BODY)
        except Exception:
            logger.debug("SandboxGuard: Redis unavailable — bypassing cap", exc_info=True)

        return await call_next(request)
