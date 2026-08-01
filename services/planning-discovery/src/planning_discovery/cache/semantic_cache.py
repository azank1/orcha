"""Semantic Caching Layer for the P&D Pipeline.

Implements multi-tier caching:
  1. Query cache — hash(task_description) → decomposition/resolution result
  2. Embedding cache — hash(query + filters) → search results
  3. Plan cache (APC) — intent-based matching for plan template reuse
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass
class CacheEntry:
    """A single cache entry with metadata."""

    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    ttl_seconds: int = 3600
    hit_count: int = 0
    cache_type: str = "generic"

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.ttl_seconds


@dataclass
class CacheStats:
    """Cache performance statistics."""

    total_gets: int = 0
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    entries: int = 0

    @property
    def hit_rate(self) -> float:
        if self.total_gets == 0:
            return 0.0
        return self.hits / self.total_gets


class SemanticCache:
    """In-memory semantic cache with TTL-based eviction.

    For production, this would be backed by Redis. The in-memory
    implementation provides the same interface for testing and
    single-process deployments.
    """

    def __init__(self, default_ttl: int = 3600, max_entries: int = 10000):
        self.default_ttl = default_ttl
        self.max_entries = max_entries
        self._store: dict[str, CacheEntry] = {}
        self.stats = CacheStats()

    @staticmethod
    def _hash_key(key_parts: list[str]) -> str:
        """Create a deterministic hash key from parts."""
        raw = "|".join(str(p) for p in key_parts)
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def get(self, key: str) -> Any | None:
        """Retrieve a value from cache."""
        self.stats.total_gets += 1
        entry = self._store.get(key)
        if entry is None:
            self.stats.misses += 1
            return None
        if entry.is_expired:
            del self._store[key]
            self.stats.misses += 1
            self.stats.evictions += 1
            self.stats.entries -= 1
            return None
        entry.hit_count += 1
        self.stats.hits += 1
        return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        cache_type: str = "generic",
    ) -> None:
        """Store a value in cache."""
        if len(self._store) >= self.max_entries:
            self._evict_expired()
            if len(self._store) >= self.max_entries:
                self._evict_lru()

        self._store[key] = CacheEntry(
            key=key,
            value=value,
            ttl_seconds=ttl or self.default_ttl,
            cache_type=cache_type,
        )
        self.stats.entries = len(self._store)

    def delete(self, key: str) -> bool:
        """Remove an entry from cache."""
        if key in self._store:
            del self._store[key]
            self.stats.entries = len(self._store)
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries."""
        self._store.clear()
        self.stats.entries = 0

    def invalidate_by_type(self, cache_type: str) -> int:
        """Invalidate all entries of a given type (e.g., on registry event)."""
        keys_to_remove = [
            k for k, v in self._store.items() if v.cache_type == cache_type
        ]
        for k in keys_to_remove:
            del self._store[k]
        self.stats.entries = len(self._store)
        self.stats.evictions += len(keys_to_remove)
        return len(keys_to_remove)

    def _evict_expired(self) -> None:
        """Remove all expired entries."""
        expired = [k for k, v in self._store.items() if v.is_expired]
        for k in expired:
            del self._store[k]
        self.stats.evictions += len(expired)

    def _evict_lru(self) -> None:
        """Evict least-recently-used entry (lowest hit count, oldest)."""
        if not self._store:
            return
        # Evict the entry with lowest hit_count, breaking ties by oldest
        lru_key = min(
            self._store.keys(),
            key=lambda k: (self._store[k].hit_count, -self._store[k].created_at),
        )
        del self._store[lru_key]
        self.stats.evictions += 1


class PipelineCache:
    """Specialized cache for the P&D pipeline with typed sub-caches.

    Provides convenience methods for caching decomposition results,
    search results, and plan templates.
    """

    def __init__(
        self,
        query_ttl: int = 3600,  # 1 hour
        embedding_ttl: int = 300,  # 5 minutes
        plan_ttl: int = 86400,  # 24 hours
    ):
        self.cache = SemanticCache(default_ttl=query_ttl)
        self.query_ttl = query_ttl
        self.embedding_ttl = embedding_ttl
        self.plan_ttl = plan_ttl

    # ── Query Cache ───────────────────────────────────────────────────

    def get_decomposition(self, query: str) -> dict[str, Any] | None:
        """Look up cached decomposition for a query."""
        key = self.cache._hash_key(["decomp", query.strip().lower()])
        return self.cache.get(key)

    def set_decomposition(self, query: str, result: dict[str, Any]) -> None:
        """Cache a decomposition result."""
        key = self.cache._hash_key(["decomp", query.strip().lower()])
        self.cache.set(key, result, ttl=self.query_ttl, cache_type="decomposition")

    # ── Embedding/Search Cache ────────────────────────────────────────

    def get_search_results(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]] | None:
        """Look up cached search results."""
        filter_str = json.dumps(filters or {}, sort_keys=True)
        key = self.cache._hash_key(["search", query, filter_str])
        return self.cache.get(key)

    def set_search_results(
        self,
        query: str,
        filters: dict[str, Any] | None,
        results: list[dict[str, Any]],
    ) -> None:
        """Cache search results."""
        filter_str = json.dumps(filters or {}, sort_keys=True)
        key = self.cache._hash_key(["search", query, filter_str])
        self.cache.set(key, results, ttl=self.embedding_ttl, cache_type="search")

    # ── Plan Template Cache (APC) ─────────────────────────────────────

    def get_plan_template(self, intent: str) -> dict[str, Any] | None:
        """Look up cached plan template by intent."""
        key = self.cache._hash_key(["plan", intent.strip().lower()])
        return self.cache.get(key)

    def set_plan_template(self, intent: str, plan: dict[str, Any]) -> None:
        """Cache a plan template for reuse."""
        key = self.cache._hash_key(["plan", intent.strip().lower()])
        self.cache.set(key, plan, ttl=self.plan_ttl, cache_type="plan_template")

    # ── Registry Event Handling ───────────────────────────────────────

    def on_agent_registered(self) -> int:
        """Invalidate search caches when a new agent registers."""
        return self.cache.invalidate_by_type("search")

    @property
    def stats(self) -> CacheStats:
        return self.cache.stats
