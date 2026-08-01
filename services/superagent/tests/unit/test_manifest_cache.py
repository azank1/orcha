"""Unit tests for ManifestCache."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from superagent.middleware.manifest_cache import ManifestCache


@pytest.fixture
def cache():
    return ManifestCache()


@pytest.mark.asyncio
async def test_cache_hit_returns_cached(cache):
    manifest = {"agent_id": "agent-1", "name": "Test Agent", "health_status": "HEALTHY"}
    with patch.object(
        cache, "_fetch", new_callable=AsyncMock, return_value=manifest
    ) as mock_fetch:
        # First call — fetches
        r1 = await cache.get_manifest("agent-1")
        # Second call — should use cache
        r2 = await cache.get_manifest("agent-1")
        assert mock_fetch.call_count == 1
    assert r1 == r2 == manifest


@pytest.mark.asyncio
async def test_cache_miss_fetches(cache):
    manifest = {"agent_id": "agent-2", "health_status": "HEALTHY"}
    with patch.object(cache, "_fetch", new_callable=AsyncMock, return_value=manifest):
        result = await cache.get_manifest("agent-2")
    assert result == manifest


@pytest.mark.asyncio
async def test_invalidate_clears_cache(cache):
    manifest = {"agent_id": "agent-3", "health_status": "HEALTHY"}
    with patch.object(
        cache, "_fetch", new_callable=AsyncMock, return_value=manifest
    ) as mock_fetch:
        await cache.get_manifest("agent-3")
        cache.invalidate("agent-3")
        await cache.get_manifest("agent-3")
        assert mock_fetch.call_count == 2


@pytest.mark.asyncio
async def test_fetch_failure_returns_empty_manifest(cache):
    with patch.object(
        cache,
        "_fetch",
        new_callable=AsyncMock,
        side_effect=Exception("Registry down"),
    ):
        # ManifestCache.get_manifest calls _fetch; if it raises, the cache records it
        # In our implementation _fetch handles exceptions internally
        pass  # _fetch is protected — test the fallback path via get_manifest with httpx mock

    with patch("httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value.__aenter__.return_value
        instance.get.side_effect = Exception("connection refused")
        result = await cache._fetch("missing-agent")
    assert result.get("agent_id") == "missing-agent"
    assert result.get("capabilities") == []
