"""User settings models."""

from __future__ import annotations

from pydantic import BaseModel


class UserSettingsResponse(BaseModel):
    user_id: str
    email: str
    display_name: str | None
    is_dev_mode: bool
    credits_usd: float

    model_config = {"json_encoders": {float: str}}


class UpdateSettingsRequest(BaseModel):
    display_name: str | None = None
    is_dev_mode: bool | None = None
