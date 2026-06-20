"""File upload routes — POST /api/v1/files/upload, GET /api/v1/files/{artifact_id}/download."""

from __future__ import annotations

import logging
import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import Response

from ..auth.models import TokenPayload
from ..dependencies import require_auth
from .models import ArtifactResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/files", tags=["files"])

_ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
    "text/markdown",
    "text/csv",
    "application/json",
    "application/yaml",
    "application/x-yaml",
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
    "audio/mpeg",
    "audio/wav",
    "video/mp4",
}
_MAX_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


@router.post("/upload", response_model=ArtifactResponse, status_code=201)
async def upload_file(
    request: Request,
    payload: Annotated[TokenPayload, Depends(require_auth)],
    file: Annotated[UploadFile, File(description="File to store as an artifact")],
    session_id: Annotated[str | None, Form()] = None,
) -> ArtifactResponse:
    """Upload a file and store it as an Artifact. Returns the artifact_id for use in messages.

    ``session_id`` is taken from multipart form field ``session_id`` (same as the UI),
    or from query string ``?session_id=`` if the form field is absent.
    """
    sid = (session_id or "").strip() or None
    if sid is None:
        sid = (request.query_params.get("session_id") or "").strip() or None

    content_type = file.content_type or "application/octet-stream"
    if content_type not in _ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{content_type}' is not supported.",
        )

    data = await file.read()
    if len(data) > _MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the 50 MB limit ({len(data)} bytes).",
        )

    artifact_id = str(uuid.uuid4())
    filename = file.filename or "upload"
    s3_key = f"artifacts/{payload.user_id}/{artifact_id}/{filename}"

    from ..config import settings
    from ..storage.s3_client import get_s3_client

    await get_s3_client().put_object(s3_key, data, content_type)

    # Persist Artifact row
    try:
        from common.database.src.generated_client import Prisma

        db = Prisma(datasource={"url": settings.database_url})
        await db.connect()
        await db.artifact.create(
            data={
                "id": artifact_id,
                "user_id": payload.user_id,
                "session_id": sid,
                "filename": filename,
                "mime_type": content_type,
                "size_bytes": len(data),
                "source": "USER_UPLOAD",
                "status": "READY",
                "s3_bucket": settings.artifact_s3_bucket,
                "s3_key": s3_key,
            }
        )
        await db.disconnect()
    except Exception:
        logger.exception("Failed to persist Artifact row for %s", artifact_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not persist artifact metadata.",
        ) from None

    logger.info(
        "Uploaded artifact %s (%s, %d bytes) for user %s",
        artifact_id,
        content_type,
        len(data),
        payload.user_id,
    )
    return ArtifactResponse(
        artifact_id=artifact_id,
        filename=filename,
        mime_type=content_type,
        size_bytes=len(data),
        session_id=sid,
    )


@router.get("/{artifact_id}/download")
async def download_file(
    artifact_id: str,
    request: Request,
    payload: Annotated[TokenPayload, Depends(require_auth)],
) -> Response:
    """Return a pre-signed S3 redirect for the artifact, or stream it directly."""
    from ..config import settings
    from ..storage.s3_client import get_s3_client

    try:
        from common.database.src.generated_client import Prisma

        db = Prisma(datasource={"url": settings.database_url})
        await db.connect()
        row = await db.artifact.find_unique(where={"id": artifact_id})
        await db.disconnect()
    except Exception:
        logger.exception("DB error fetching artifact %s", artifact_id)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE) from None

    if row is None or row.status != "READY":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found"
        )

    if row.user_id != payload.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # If LocalStack / no real AWS, stream bytes directly; otherwise redirect to pre-signed URL.
    if settings.s3_endpoint_url:
        data = await get_s3_client().get_object(row.s3_key)
        return Response(
            content=data,
            media_type=row.mime_type,
            headers={"Content-Disposition": f'attachment; filename="{row.filename}"'},
        )

    url = get_s3_client().presigned_url(row.s3_key)
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url=url)
