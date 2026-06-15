"""OutputNormalizer — converts handler results to AgentState-compatible format.

Plain text / JSON MCP results pass through unchanged. Binary MCP payloads (bytes or
content-list blobs) are uploaded via artifact_store. File paths on disk are NOT
interpreted here — the model must call save_artifact after MCP tools that write files.
"""

from __future__ import annotations

import base64
import mimetypes
from typing import Any

from ..artifact_store import persist_agent_output_bytes
from ..graph.state import ArtifactRef


class OutputNormalizer:
    """Normalises handler output into a content string and optional artifact.

    normalize() is async — it may upload binary blobs to S3.
    """

    @staticmethod
    async def normalize(
        raw_output: Any,
        protocol: str,
        session_id: str = "",
        user_id: str = "",
    ) -> dict[str, Any]:
        """
        Normalise raw handler output.

        Returns dict:
            "content"  — str content for ToolMessage
            "artifact" — ArtifactRef | None if binary content was stored
        """
        if isinstance(raw_output, str):
            return {"content": raw_output, "artifact": None}

        if isinstance(raw_output, dict):
            return await OutputNormalizer._normalise_dict(raw_output, session_id, user_id)

        if isinstance(raw_output, bytes):
            return await persist_agent_output_bytes(
                raw_output,
                "application/octet-stream",
                "output.bin",
                session_id,
                user_id,
            )

        return {"content": str(raw_output), "artifact": None}

    @staticmethod
    async def _normalise_dict(
        data: dict[str, Any], session_id: str, user_id: str
    ) -> dict[str, Any]:
        # MCP content list (list of text/image/blob items)
        content_list = data.get("content")
        if isinstance(content_list, list):
            parts: list[str] = []
            artifact: ArtifactRef | None = None
            for item in content_list:
                if not isinstance(item, dict):
                    parts.append(str(item))
                    continue
                item_type = item.get("type", "text")
                if item_type == "text":
                    parts.append(item.get("text", ""))
                elif item_type in ("image", "blob"):
                    raw = item.get("data") or item.get("blob")
                    if raw:
                        mime = item.get("mimeType", "application/octet-stream")
                        if isinstance(raw, str):
                            try:
                                raw = base64.b64decode(raw)
                            except Exception:
                                parts.append(raw)
                                continue
                        result = await persist_agent_output_bytes(
                            raw,
                            mime,
                            f"output{_ext_for_mime(mime)}",
                            session_id,
                            user_id,
                        )
                        artifact = result["artifact"]
                        if artifact:
                            parts.append(f"[Artifact: {artifact.artifact_id}]")
                else:
                    parts.append(str(item))
            return {"content": "\n".join(parts), "artifact": artifact}

        # A2A / generic text result
        text = (
            data.get("result")
            or data.get("output")
            or data.get("text")
            or data.get("message")
            or str(data)
        )
        return {"content": str(text), "artifact": None}


def _ext_for_mime(mime: str) -> str:
    ext = mimetypes.guess_extension(mime) or ""
    return ext if ext else ".bin"
