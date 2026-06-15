"""File upload response models."""

from __future__ import annotations

from pydantic import BaseModel


class ArtifactResponse(BaseModel):
    artifact_id: str
    filename: str
    mime_type: str
    size_bytes: int
    session_id: str | None
