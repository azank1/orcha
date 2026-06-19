"""Persist agent-produced artifacts to S3 and the Artifact table.

Used by OutputNormalizer (binary MCP payloads) and system tool save_artifact.
"""

from __future__ import annotations

import logging
import mimetypes
import uuid
from pathlib import Path
from .graph.state import ArtifactRef

logger = logging.getLogger(__name__)


def artifact_produced_tool_message(
    artifact_id: str, filename: str, mime_type: str
) -> str:
    """Short summary for ToolMessage after a successful upload."""
    return (
        f"[ARTIFACT PRODUCED]\n"
        f"ID: {artifact_id} | Filename: {filename} | Type: {mime_type}\n"
        f"Share this artifact_id with the user; downloads go through the gateway. "
        f"For parsing uploads: stage_artifact then doc-parse file_path. "
        f"For MCP-written files under /tmp: save_artifact(local_path=…)."
    )


async def create_artifact_row(
    *,
    artifact_id: str,
    user_id: str,
    session_id: str | None,
    filename: str,
    mime_type: str,
    size_bytes: int,
    s3_bucket: str,
    s3_key: str,
    source: str,
) -> None:
    """Persist an Artifact row to the database."""
    try:
        from src.generated_client import Prisma

        db = Prisma()
        await db.connect()
        await db.artifact.create(
            data={
                "id": artifact_id,
                "user_id": user_id,
                "session_id": session_id,
                "filename": filename,
                "mime_type": mime_type,
                "size_bytes": size_bytes,
                "source": source,
                "status": "READY",
                "s3_bucket": s3_bucket,
                "s3_key": s3_key,
            }
        )
        await db.disconnect()
    except Exception:
        logger.exception("Failed to create Artifact DB row for %s", artifact_id)


async def persist_agent_output_bytes(
    data: bytes,
    mime_type: str,
    filename: str,
    session_id: str,
    user_id: str,
) -> dict[str, Any]:
    """Upload bytes to S3, create Artifact row, return normalised pipeline dict."""
    artifact_id = str(uuid.uuid4())

    try:
        from .config import settings
        from .storage.s3_client import get_s3_client

        s3_key = f"artifacts/{user_id}/{artifact_id}/{filename}"
        s3_bucket = settings.artifact_s3_bucket
        await get_s3_client().put_object(s3_key, data, mime_type)

        await create_artifact_row(
            artifact_id=artifact_id,
            user_id=user_id,
            session_id=session_id or None,
            filename=filename,
            mime_type=mime_type,
            size_bytes=len(data),
            s3_bucket=s3_bucket,
            s3_key=s3_key,
            source="AGENT_OUTPUT",
        )

        ref = ArtifactRef(
            artifact_id=artifact_id,
            filename=filename,
            mime_type=mime_type,
            size_bytes=len(data),
            s3_bucket=s3_bucket,
            s3_key=s3_key,
        )
        logger.info(
            "Stored AGENT_OUTPUT artifact %s (%s, %d bytes)",
            artifact_id,
            mime_type,
            len(data),
        )
        return {
            "content": artifact_produced_tool_message(artifact_id, filename, mime_type),
            "artifact": ref,
        }
    except Exception:
        logger.exception("Failed to upload artifact %s to S3", artifact_id)
        ref = ArtifactRef(
            artifact_id=artifact_id,
            filename=filename,
            mime_type=mime_type,
            size_bytes=len(data),
            s3_bucket="",
            s3_key="",
        )
        return {"content": f"[Artifact: {artifact_id}]", "artifact": ref}


async def persist_agent_output_file(
    file_path: Path,
    session_id: str,
    user_id: str,
    *,
    target_filename: str | None = None,
    mime_type_override: str | None = None,
) -> dict[str, Any]:
    """Read a local file, upload as AGENT_OUTPUT, return same shape as persist_agent_output_bytes."""
    try:
        data = file_path.read_bytes()
    except OSError:
        logger.exception("Failed to read file %s", file_path)
        return {"content": f"Error: could not read {file_path}", "artifact": None}

    guessed, _ = mimetypes.guess_type(str(file_path))
    mime_type = mime_type_override or guessed or "application/octet-stream"
    filename = Path(target_filename).name if target_filename else file_path.name
    return await persist_agent_output_bytes(
        data, mime_type, filename, session_id, user_id
    )


def save_artifact_success_payload(ref: ArtifactRef) -> dict[str, Any]:
    """Structured return for save_artifact system tool + execute_agent_calls state merge."""
    return {
        "ok": True,
        "artifact_id": ref.artifact_id,
        "filename": ref.filename,
        "mime_type": ref.mime_type,
        "size_bytes": ref.size_bytes,
        "s3_bucket": ref.s3_bucket,
        "s3_key": ref.s3_key,
    }
