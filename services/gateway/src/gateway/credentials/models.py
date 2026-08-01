"""Credential request models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class StoreCredentialRequest(BaseModel):
    agent_id: str
    var_name: str
    value: str
    scope: str = Field("permanent", pattern="^(permanent|session)$")
    session_id: str | None = None  # required when scope="session"


class DeleteCredentialRequest(BaseModel):
    agent_id: str
    var_name: str
    scope: str = Field("permanent", pattern="^(permanent|session)$")
    session_id: str | None = None  # required when scope="session"
