"""Global error handler middleware for the Planning & Discovery service."""

from __future__ import annotations

import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Catch-all middleware that converts unhandled exceptions into a
    standardised JSON error envelope, preventing raw tracebacks from
    leaking to clients.
    """

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        try:
            return await call_next(request)
        except Exception:
            logger.exception(
                "Unhandled exception in %s %s", request.method, request.url.path
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "An internal server error occurred",
                    "path": request.url.path,
                },
            )
