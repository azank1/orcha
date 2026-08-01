"""Facebook Graph API tools — Page publishing and engagement.

All functions use Meta Graph API v19.0.
Returns mock payloads when FB_ACCESS_TOKEN or FB_PAGE_ID are absent — unless
REQUIRE_LIVE_CREDENTIALS=true, in which case they raise instead (see
._production_guard).
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_GRAPH_BASE = "https://graph.facebook.com/v19.0"


def _is_configured() -> bool:
    from ._production_guard import require_configured
    configured = bool(os.getenv("FB_ACCESS_TOKEN")) and bool(os.getenv("FB_PAGE_ID"))
    return require_configured(configured, "Facebook", "FB_ACCESS_TOKEN / FB_PAGE_ID")


def _token() -> str:
    return os.getenv("FB_ACCESS_TOKEN", "")


def _page_id() -> str:
    return os.getenv("FB_PAGE_ID", "")


async def create_post(message: str) -> dict[str, Any]:
    """Publish a text post to the Facebook Page."""
    if not _is_configured():
        return {"status": "mock", "id": "mock_page_mock_post_001", "message": message}
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.post(
                f"{_GRAPH_BASE}/{_page_id()}/feed",
                params={"access_token": _token()},
                json={"message": message},
            )
            resp.raise_for_status()
            return {"status": "ok", **resp.json()}
        except Exception as exc:
            logger.warning("create_post failed: %s", exc)
            return {"status": "error", "error": str(exc)}


async def get_page_posts(limit: int = 10) -> dict[str, Any]:
    """Retrieve the most recent posts from the Facebook Page."""
    if not _is_configured():
        return {
            "status": "mock",
            "data": [
                {"id": f"mock_post_{i}", "message": f"Mock post #{i}", "created_time": "2026-04-10T00:00:00+0000"}
                for i in range(1, 4)
            ],
        }
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.get(
                f"{_GRAPH_BASE}/{_page_id()}/posts",
                params={"access_token": _token(), "limit": limit, "fields": "id,message,created_time"},
            )
            resp.raise_for_status()
            return {"status": "ok", **resp.json()}
        except Exception as exc:
            logger.warning("get_page_posts failed: %s", exc)
            return {"status": "error", "error": str(exc)}


async def delete_post(post_id: str) -> dict[str, Any]:
    """Delete a post from the Facebook Page."""
    if not _is_configured():
        return {"status": "mock", "success": True, "post_id": post_id}
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.delete(
                f"{_GRAPH_BASE}/{post_id}",
                params={"access_token": _token()},
            )
            resp.raise_for_status()
            return {"status": "ok", **resp.json()}
        except Exception as exc:
            logger.warning("delete_post failed id=%s: %s", post_id, exc)
            return {"status": "error", "error": str(exc)}


async def post_image(image_url: str, caption: str = "") -> dict[str, Any]:
    """Publish an image to the Facebook Page from a public URL."""
    if not _is_configured():
        return {"status": "mock", "id": "mock_photo_001", "post_id": "mock_photo_post_001"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                f"{_GRAPH_BASE}/{_page_id()}/photos",
                params={"access_token": _token()},
                json={"url": image_url, "caption": caption},
            )
            resp.raise_for_status()
            return {"status": "ok", **resp.json()}
        except Exception as exc:
            logger.warning("post_image failed: %s", exc)
            return {"status": "error", "error": str(exc)}


async def get_post_comments(post_id: str) -> dict[str, Any]:
    """Get comments on a Facebook Page post."""
    if not _is_configured():
        return {
            "status": "mock",
            "data": [{"id": "mock_comment_1", "message": "Great product!", "from": {"name": "Mock User"}}],
        }
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.get(
                f"{_GRAPH_BASE}/{post_id}/comments",
                params={"access_token": _token(), "fields": "id,message,from,created_time"},
            )
            resp.raise_for_status()
            return {"status": "ok", **resp.json()}
        except Exception as exc:
            logger.warning("get_post_comments failed id=%s: %s", post_id, exc)
            return {"status": "error", "error": str(exc)}


async def get_number_of_comments(post_id: str) -> dict[str, Any]:
    """Get the comment count summary for a Facebook Page post."""
    if not _is_configured():
        return {"status": "mock", "post_id": post_id, "count": 17}
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.get(
                f"{_GRAPH_BASE}/{post_id}",
                params={"access_token": _token(), "fields": "comments.summary(true)"},
            )
            resp.raise_for_status()
            data = resp.json()
            count = data.get("comments", {}).get("summary", {}).get("total_count", 0)
            return {"status": "ok", "post_id": post_id, "count": count}
        except Exception as exc:
            logger.warning("get_number_of_comments failed id=%s: %s", post_id, exc)
            return {"status": "error", "error": str(exc)}


async def reply_to_comment(comment_id: str, message: str) -> dict[str, Any]:
    """Reply to a comment on a Facebook Page post."""
    if not _is_configured():
        return {"status": "mock", "id": "mock_reply_001", "comment_id": comment_id}
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.post(
                f"{_GRAPH_BASE}/{comment_id}/comments",
                params={"access_token": _token()},
                json={"message": message},
            )
            resp.raise_for_status()
            return {"status": "ok", **resp.json()}
        except Exception as exc:
            logger.warning("reply_to_comment failed id=%s: %s", comment_id, exc)
            return {"status": "error", "error": str(exc)}


async def get_number_of_likes(post_id: str) -> dict[str, Any]:
    """Get the like/reaction count summary for a Facebook Page post."""
    if not _is_configured():
        return {"status": "mock", "post_id": post_id, "count": 42}
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.get(
                f"{_GRAPH_BASE}/{post_id}",
                params={"access_token": _token(), "fields": "likes.summary(true)"},
            )
            resp.raise_for_status()
            data = resp.json()
            count = data.get("likes", {}).get("summary", {}).get("total_count", 0)
            return {"status": "ok", "post_id": post_id, "count": count}
        except Exception as exc:
            logger.warning("get_number_of_likes failed id=%s: %s", post_id, exc)
            return {"status": "error", "error": str(exc)}
