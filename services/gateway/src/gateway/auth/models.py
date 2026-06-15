"""Auth request/response models."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class TokenPayload(BaseModel):
    user_id: str
    email: str
    jti: str  # JWT ID — used for revocation


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    display_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
