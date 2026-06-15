"""Instagram Graph API tools — profile, media, insights, publishing.

All functions use Instagram Graph API via Meta's graph.facebook.com/v19.0 endpoint.
Returns mock payloads when IG_ACCESS_TOKEN or IG_USER_ID are absent.

Publishing is a 2-step process per Meta spec:
  1. POST /{ig_user_id}/media  → creates a container, returns container_id
  2. Poll container until status_code = FINISHED
  3. POST /{ig_user_id}/media_publish with creation_id → publishes, returns media_id
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_GRAPH_BASE = "https://graph.facebook.com/v19.0"


def _is_configured() -> bool:
    return bool(os.getenv("IG_ACCESS_TOKEN")) and bool(os.getenv("IG_USER_ID"))


def _token() -> str:
    return os.getenv("IG_ACCESS_TOKEN", "")


def _user_id() -> str:
    return os.getenv("IG_USER_ID", "")


async def get_profile_info() -> dict[str, Any]:
    """Fetch Instagram Business account profile information."""
    if not _is_configured():
        return {
            "status": "mock",
            "id": "mock_ig_user",
            "username": "mock_store",
            "name": "Mock Store",
            "followers_count": 12400,
            "follows_count": 380,
            "media_count": 217,
            "biography": "Mock Instagram profile for demo purposes.",
            "website": "https://mockstore.example.com",
        }
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.get(
                f"{_GRAPH_BASE}/{_user_id()}",
                params={
                    "access_token": _token(),
                    "fields": "id,username,name,biography,followers_count,follows_count,media_count,website,profile_picture_url",
                },
            )
            resp.raise_for_status()
            return {"status": "ok", **resp.json()}
        except Exception as exc:
            logger.warning("get_profile_info failed: %s", exc)
            return {"status": "error", "error": str(exc)}


async def get_media_posts(limit: int = 10) -> dict[str, Any]:
    """Fetch recent media posts from the Instagram Business account."""
    if not _is_configured():
        return {
            "status": "mock",
            "data": [
                {
                    "id": f"mock_media_{i}",
                    "caption": f"Mock Instagram post #{i} — check out our latest products!",
                    "media_type": "IMAGE",
                    "timestamp": "2026-04-10T00:00:00+0000",
                    "permalink": f"https://www.instagram.com/p/mockpost{i}/",
                }
                for i in range(1, 4)
            ],
        }
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.get(
                f"{_GRAPH_BASE}/{_user_id()}/media",
                params={
                    "access_token": _token(),
                    "limit": limit,
                    "fields": "id,caption,media_type,media_url,thumbnail_url,timestamp,permalink,like_count,comments_count",
                },
            )
            resp.raise_for_status()
            return {"status": "ok", **resp.json()}
        except Exception as exc:
            logger.warning("get_media_posts failed: %s", exc)
            return {"status": "error", "error": str(exc)}


async def get_media_insights(media_id: str) -> dict[str, Any]:
    """Fetch insights (impressions, reach, likes, comments, saved) for a media post."""
    if not _is_configured():
        return {
            "status": "mock",
            "media_id": media_id,
            "insights": {
                "impressions": 3840,
                "reach": 2910,
                "likes": 187,
                "comments": 23,
                "saved": 41,
                "shares": 15,
            },
        }
    metrics = ["impressions", "reach", "likes", "comments", "saved", "shares"]
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.get(
                f"{_GRAPH_BASE}/{media_id}/insights",
                params={
                    "access_token": _token(),
                    "metric": ",".join(metrics),
                },
            )
            resp.raise_for_status()
            raw = resp.json()
            insights = {item["name"]: item.get("values", [{}])[0].get("value", 0) for item in raw.get("data", [])}
            return {"status": "ok", "media_id": media_id, "insights": insights}
        except Exception as exc:
            logger.warning("get_media_insights failed id=%s: %s", media_id, exc)
            return {"status": "error", "error": str(exc)}


async def publish_media(image_url: str, caption: str = "") -> dict[str, Any]:
    """Publish an image to Instagram (2-step: create container → publish).

    The image must be publicly accessible via HTTPS.
    """
    if not _is_configured():
        return {
            "status": "mock",
            "id": "mock_ig_media_001",
            "caption": caption,
            "permalink": "https://www.instagram.com/p/mockdemo001/",
        }
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Step 1: create media container
            container_resp = await client.post(
                f"{_GRAPH_BASE}/{_user_id()}/media",
                params={"access_token": _token()},
                json={"image_url": image_url, "caption": caption},
            )
            container_resp.raise_for_status()
            container_id = container_resp.json().get("id")
            if not container_id:
                return {"status": "error", "error": "No container ID returned from Instagram"}

            # Step 2: poll until container is FINISHED (max 10 attempts)
            for _ in range(10):
                await asyncio.sleep(3)
                status_resp = await client.get(
                    f"{_GRAPH_BASE}/{container_id}",
                    params={"access_token": _token(), "fields": "status_code"},
                )
                status_resp.raise_for_status()
                code = status_resp.json().get("status_code", "")
                if code == "FINISHED":
                    break
                if code == "ERROR":
                    return {"status": "error", "error": "Instagram container processing failed"}

            # Step 3: publish the container
            publish_resp = await client.post(
                f"{_GRAPH_BASE}/{_user_id()}/media_publish",
                params={"access_token": _token()},
                json={"creation_id": container_id},
            )
            publish_resp.raise_for_status()
            media_id = publish_resp.json().get("id")
            return {"status": "ok", "id": media_id, "caption": caption}
        except Exception as exc:
            logger.warning("publish_media failed: %s", exc)
            return {"status": "error", "error": str(exc)}
