"""Workflow request/response models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CreateWorkflowRequest(BaseModel):
    session_id: str
    name: str
    description: str | None = None


class UpdateWorkflowRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = Field(None, pattern="^(active|inactive|scheduled)$")


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str | None
    goal_template: str
    status: str
    agents_used: list[str]
    steps: Any
    run_count: int
    created_at: datetime
    updated_at: datetime
