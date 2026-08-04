"""Mock-mode fallback tests for ecommerce-automation.

API credentials are cleared by conftest.py, so all tool functions return
mock payloads. The FastAPI TestClient verifies server-level behaviour
(health, agent card, skill routing) without starting a real server.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from src.tools.shopify import create_product, get_products
from src.tools.facebook import create_post
from src.tools.instagram import get_profile_info
from src.a2a_server import app

client = TestClient(app)


# ── Tool mock-fallback tests ──────────────────────────────────────────────────

async def test_create_product_mock():
    result = await create_product("Air Max 90", price="149.99")
    assert isinstance(result, dict)
    assert result["status"] == "mock"


async def test_get_products_mock():
    result = await get_products(limit=5)
    assert isinstance(result, dict)
    assert result["status"] == "mock"
    assert "products" in result


async def test_create_post_mock():
    result = await create_post("New arrivals just dropped!")
    assert isinstance(result, dict)
    assert result["status"] == "mock"


async def test_get_profile_info_mock():
    result = await get_profile_info()
    assert isinstance(result, dict)
    assert result["status"] == "mock"


# ── HTTP layer tests (FastAPI TestClient) ─────────────────────────────────────

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "shopify_configured" in data
    assert "facebook_configured" in data
    assert "instagram_configured" in data


def test_agent_card_has_three_skills():
    response = client.get("/.well-known/agent.json")
    assert response.status_code == 200
    data = response.json()
    skill_ids = {s["id"] for s in data["skills"]}
    assert skill_ids == {"shopify_management", "social_publishing", "store_analytics"}


def _send(task_id: str, text: str) -> dict:
    payload = {
        "id": task_id,
        "message": {"parts": [{"type": "text", "text": text}]},
    }
    r = client.post("/a2a/tasks/send", json=payload)
    assert r.status_code == 200
    assert r.json()["status"]["state"] == "completed"
    return json.loads(r.json()["status"]["message"]["parts"][0]["text"])


def test_task_routes_to_shopify():
    result = _send("t-1", "list shopify products")
    assert result["skill"] == "shopify_management"


def test_task_routes_to_social_publishing():
    result = _send("t-2", "post to instagram")
    assert result["skill"] == "social_publishing"


def test_task_routes_to_store_analytics():
    result = _send("t-3", "how many likes does the post have")
    assert result["skill"] == "store_analytics"
