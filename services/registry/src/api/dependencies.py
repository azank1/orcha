"""FastAPI dependencies for authentication and database."""

import os
from typing import Annotated

from common.database.src.generated_client import Prisma
from fastapi import Header, HTTPException, status

from common.utils.src.auth import validate_pat_token_format, verify_pat_token

# Global database instance
db = Prisma()


async def get_db() -> Prisma:
    """
    Get database instance.

    Returns:
        Prisma client
    """
    return db


def _decode_jwt_user_id(authorization: str | None) -> str | None:
    """Extract user_id from a JWT Bearer token without verifying the signature.

    Used when DISABLE_AUTH=true so callers that pass a real gateway JWT still
    get their actual user_id mapped to the registered agent.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        import base64
        import json as _json

        payload_b64 = parts[1]
        # Add padding so base64 doesn't complain
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = _json.loads(base64.urlsafe_b64decode(payload_b64))
        return payload.get("sub") or None
    except Exception:
        return None


async def verify_token(authorization: Annotated[str | None, Header()] = None) -> str:
    """
    Verify PAT token from Authorization header.

    Args:
        authorization: Authorization header value

    Returns:
        User ID if token is valid

    Raises:
        HTTPException: If token is invalid
    """
    # Auth disabled — still try to extract real user_id from JWT if one is present.
    # Seed scripts / CLI tools without a token fall back to "dev_user".
    if os.getenv("DISABLE_AUTH", "false").lower() == "true":
        return _decode_jwt_user_id(authorization) or "dev_user"

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )

    # Extract token from "Bearer <token>" format
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'",
        )

    token = authorization[7:]  # Remove "Bearer " prefix

    # Validate token format
    if not validate_pat_token_format(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid PAT token format"
        )

    # Query database for user with matching token
    user = await db.user.find_first(where={"is_active": True})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

    # Verify token hash
    if not verify_pat_token(token, user.pat_token_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

    return user.id
