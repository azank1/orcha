"""User settings routes."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..auth.models import TokenPayload
from ..dependencies import require_auth
from .models import UpdateSettingsRequest, UserSettingsResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


@router.get("/me", response_model=UserSettingsResponse)
async def get_settings(
    request: Request,
    payload: Annotated[TokenPayload, Depends(require_auth)],
) -> UserSettingsResponse:
    db = request.app.state.db
    user = await db.user.find_unique(where={"id": payload.user_id})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return UserSettingsResponse(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        is_dev_mode=user.is_dev_mode,
        credits_usd=user.credits_usd,
    )


@router.patch("/me", response_model=UserSettingsResponse)
async def update_settings(
    body: UpdateSettingsRequest,
    request: Request,
    payload: Annotated[TokenPayload, Depends(require_auth)],
) -> UserSettingsResponse:
    db = request.app.state.db
    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )
    user = await db.user.update(where={"id": payload.user_id}, data=update_data)
    return UserSettingsResponse(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        is_dev_mode=user.is_dev_mode,
        credits_usd=user.credits_usd,
    )
