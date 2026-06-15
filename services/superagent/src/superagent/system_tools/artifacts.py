"""Artifact system tools — read metadata, stage S3 uploads to /tmp, persist disk files to S3."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .registry import SystemToolRegistry, SystemToolSpec

logger = logging.getLogger(__name__)


def _session_tmp_root(session_id: str) -> Path:
    return Path("/tmp") / session_id  # noqa: S108


def _resolved_is_under_session_workspace(path: Path, session_id: str) -> bool:
    """True if resolved path is a file under /tmp/{session_id}/."""
    if not session_id:
        return False
    try:
        root = _session_tmp_root(session_id).resolve()
        resolved = path.expanduser().resolve()
        resolved.relative_to(root)
    except (ValueError, OSError):
        return False
    return resolved.is_file()


async def _read_artifact(args: dict[str, Any], state: dict[str, Any]) -> Any:
    """Return metadata about a stored artifact."""
    artifact_id = args["artifact_id"]
    artifacts: dict[str, Any] = state.get("artifacts", {})
    ref = artifacts.get(artifact_id)
    if ref is None:
        return {"error": f"Artifact {artifact_id!r} not found in session"}
    return {
        "artifact_id": artifact_id,
        "filename": getattr(ref, "filename", ""),
        "mime_type": getattr(ref, "mime_type", "application/octet-stream"),
        "size_bytes": getattr(ref, "size_bytes", 0),
        "s3_key": getattr(ref, "s3_key", ""),
    }


async def _stage_artifact(args: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    """Copy artifact bytes from S3 to /tmp/{session_id}/… for doc-parse / doc-convert file_path.

    Returns a small JSON payload (path only) — never file body in the LLM context.
    """
    from ..storage.s3_client import get_s3_client

    session_id = (state.get("session_id") or "").strip()
    if not session_id:
        return {"error": "session_id is required to stage files under /tmp"}

    artifact_id = str(args.get("artifact_id", "")).strip()
    if not artifact_id:
        return {"error": "artifact_id is required"}

    artifacts: dict[str, Any] = state.get("artifacts", {})
    ref = artifacts.get(artifact_id)
    if ref is None:
        return {"error": f"Artifact {artifact_id!r} not found in session"}

    s3_key = getattr(ref, "s3_key", "") or ""
    if not s3_key:
        return {"error": "Artifact has no S3 key"}

    base = _session_tmp_root(session_id)
    staged_dir = base / "staged" / artifact_id
    try:
        staged_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.exception("Could not create staging directory")
        return {"error": f"Could not create staging directory: {exc}"}

    raw_name = args.get("filename") or getattr(ref, "filename", "") or "file"
    safe_name = Path(str(raw_name)).name or "file"

    dest = (staged_dir / safe_name).resolve()
    try:
        _ = dest.relative_to(staged_dir.resolve())
    except ValueError:
        return {"error": "Invalid destination path"}

    try:
        s3 = get_s3_client()
        raw_bytes = await s3.get_object(s3_key)
        dest.write_bytes(raw_bytes)
    except Exception as exc:
        logger.exception("Failed to stage artifact %s", artifact_id)
        return {"error": f"Failed to stage artifact: {exc}"}

    mime = getattr(ref, "mime_type", "application/octet-stream")
    return {
        "path": str(dest),
        "artifact_id": artifact_id,
        "filename": safe_name,
        "mime_type": mime,
        "size_bytes": len(raw_bytes),
    }


async def _save_artifact(args: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    """Read a file under /tmp/{session_id}/, upload as AGENT_OUTPUT, return artifact metadata."""
    from ..artifact_store import persist_agent_output_file, save_artifact_success_payload

    session_id = (state.get("session_id") or "").strip()
    user_id = (state.get("user_id") or "").strip()
    if not session_id:
        return {"ok": False, "error": "session_id is required"}
    if not user_id:
        return {"ok": False, "error": "user_id is required"}

    raw_path = args.get("local_path") or args.get("path")
    if not raw_path or not isinstance(raw_path, str):
        return {
            "ok": False,
            "error": "local_path or path is required (absolute file under session /tmp)",
        }

    file_path = Path(raw_path.strip())
    if not _resolved_is_under_session_workspace(file_path, session_id):
        return {
            "ok": False,
            "error": (
                f"local_path must resolve to an existing file under "
                f"/tmp/{session_id}/"
            ),
        }

    raw_fn = args.get("filename")
    target_filename: str | None = None
    if isinstance(raw_fn, str) and raw_fn.strip():
        target_filename = raw_fn.strip()
    raw_mime = args.get("mime_type")
    mime_override: str | None = None
    if isinstance(raw_mime, str) and raw_mime.strip():
        mime_override = raw_mime.strip()

    out = await persist_agent_output_file(
        file_path.resolve(),
        session_id,
        user_id,
        target_filename=target_filename,
        mime_type_override=mime_override,
    )
    ref = out.get("artifact")
    if ref is None or not getattr(ref, "s3_key", ""):
        msg = out.get("content", "Failed to persist artifact")
        return {"ok": False, "error": str(msg)}

    return save_artifact_success_payload(ref)


def register_artifact_tools(registry: SystemToolRegistry) -> None:
    registry.register(
        SystemToolSpec(
            name="read_artifact",
            description="Read metadata about a stored artifact (filename, MIME type, size).",
            parameters={
                "type": "object",
                "properties": {
                    "artifact_id": {
                        "type": "string",
                        "description": "ID of the artifact",
                    },
                },
                "required": ["artifact_id"],
            },
            handler=_read_artifact,
        )
    )
    registry.register(
        SystemToolSpec(
            name="stage_artifact",
            description=(
                "Stage a session artifact from S3 to a local file under /tmp/{session_id}/. "
                "Returns JSON with `path` only — use that path as file_path / source_path for "
                "doc-parse or doc-convert. Never pull full file bytes into the model context."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "artifact_id": {
                        "type": "string",
                        "description": "Session artifact id (from uploads or prior tool output)",
                    },
                    "filename": {
                        "type": "string",
                        "description": "Optional basename for the staged file (defaults to artifact filename)",
                    },
                },
                "required": ["artifact_id"],
            },
            handler=_stage_artifact,
        )
    )
    registry.register(
        SystemToolSpec(
            name="save_artifact",
            description=(
                "Persist a file already on disk (e.g. doc-convert output_path) as a downloadable "
                "artifact. Pass local_path absolute under /tmp/{session_id}/. After MCP tools that "
                "return JSON with output_path, call save_artifact with that path."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "local_path": {
                        "type": "string",
                        "description": "Absolute path to an existing file under /tmp/{session_id}/",
                    },
                    "path": {
                        "type": "string",
                        "description": "Alias for local_path (same semantics)",
                    },
                    "filename": {
                        "type": "string",
                        "description": "Optional filename stored with the artifact (basename only)",
                    },
                    "mime_type": {
                        "type": "string",
                        "description": "Optional MIME type override",
                    },
                },
                "required": [],
            },
            handler=_save_artifact,
        )
    )
