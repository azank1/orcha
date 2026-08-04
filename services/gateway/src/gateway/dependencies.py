"""Shared FastAPI dependencies."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .auth.jwt import decode_access_token
from .auth.models import TokenPayload

logger = logging.getLogger(__name__)

_bearer = HTTPBearer()


async def require_auth(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Security(_bearer)],
) -> TokenPayload:
    """Validate JWT and check revocation set in Redis."""
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    redis = request.app.state.redis
    if await redis.sismember("jwt:revoked", payload.jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


async def require_dev_mode(
    request: Request,
    payload: Annotated[TokenPayload, Depends(require_auth)],
) -> TokenPayload:
    """Require that the authenticated user has dev mode enabled."""
    db = request.app.state.db
    user = await db.user.find_unique(where={"id": payload.user_id})
    if user is None or not user.is_dev_mode:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Developer mode is not enabled for this account",
        )
    return payload
