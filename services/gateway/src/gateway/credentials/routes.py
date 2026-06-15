"""Credential management routes."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel

from ..auth.models import TokenPayload
from ..dependencies import require_auth
from .models import DeleteCredentialRequest, StoreCredentialRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/credentials", tags=["credentials"])


class AgentSecretItem(BaseModel):
    agent_id: str
    agent_name: str
    var_name: str
    description: str | None
    required: bool


_SESSION_CRED_TTL = 3600  # 1 hour


@router.post("", status_code=204)
async def store_credential(
    body: StoreCredentialRequest,
    request: Request,
    payload: Annotated[TokenPayload, Depends(require_auth)],
) -> None:
    if body.scope == "permanent":
        sa = request.app.state.superagent
        resp = await sa.post(
            "/secrets/agent-env",
            json={
                "user_id": payload.user_id,
                "agent_id": body.agent_id,
                "credentials": {body.var_name: body.value},
            },
        )
        resp.raise_for_status()
    else:
        if not body.session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="session_id is required for session-scoped credentials",
            )
        redis = request.app.state.redis
        key = f"gateway:creds:session:{body.session_id}:{body.agent_id}:{body.var_name}"
        await redis.set(key, body.value, ex=_SESSION_CRED_TTL)


@router.delete("", status_code=204)
async def delete_credential(
    body: DeleteCredentialRequest,
    request: Request,
    payload: Annotated[TokenPayload, Depends(require_auth)],
) -> None:
    if body.scope == "permanent":
        sa = request.app.state.superagent
        resp = await sa.delete(
            f"/secrets/agent-env/{body.agent_id}/{body.var_name}",
            params={"user_id": payload.user_id},
        )
        resp.raise_for_status()
    else:
        if not body.session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="session_id is required for session-scoped credentials",
            )
        redis = request.app.state.redis
        key = f"gateway:creds:session:{body.session_id}:{body.agent_id}:{body.var_name}"
        await redis.delete(key)


@router.get("/required", response_model=list[AgentSecretItem])
async def get_required_secrets(
    request: Request,
    payload: Annotated[TokenPayload, Depends(require_auth)],
    agent_ids: Annotated[list[str], Query(alias="agent_ids")] = None,  # type: ignore[assignment]
) -> list[AgentSecretItem]:
    """Return the runtime secrets required by the given agents."""
    if not agent_ids:
        return []
    db = request.app.state.db
    records = await db.agentsecret.find_many(
        where={"agent_id": {"in": agent_ids}},
        include={"agent": True},
    )
    return [
        AgentSecretItem(
            agent_id=r.agent_id,
            agent_name=r.agent.name if r.agent else r.agent_id,
            var_name=r.var_name,
            description=r.description,
            required=r.required,
        )
        for r in records
    ]
