"""platform_mcp_baseline — boot-time cache of system MCP tool schemas.

Called once during lifespan (after PlatformToolSeeder.seed) so that the
orchestrator exposes system MCP tools to the LLM even when pnd_gate() is False.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_baseline_candidates: list[dict[str, Any]] = []
_baseline_openai_tools: list[dict[str, Any]] = []


def _missing_platform_env_keys(manifest: dict[str, Any]) -> list[str]:
    """Return env keys declared as platform_env but absent or empty in os.environ.

    Checks truthiness, not just presence — kept in lockstep with
    PlatformToolSeeder._missing_platform_env_keys() (inlined here to avoid
    coupling this module to RegistryClient). A `KEY=` placeholder in `.env`
    must still count as unconfigured, or the LLM is offered a tool it cannot
    actually call and will pick it over a correctly-configured alternative.
    """
    missing: list[str] = []
    strategies = manifest.get("security", {}).get("auth_strategies", []) or []
    for strategy in strategies:
        if strategy.get("type") == "platform_env":
            key = (strategy.get("config") or {}).get("env_key", "")
            if key and not os.environ.get(key):
                missing.append(key)
    return missing


def load_baseline_from_manifests(emerge_tools_dir: str) -> None:
    """Read manifests and populate module-level baseline caches.

    Filters to manifests where:
      - protocol.type == "mcp"
      - capabilities.tools is non-empty
      - no missing platform_env keys in os.environ

    Safe to call multiple times — each call replaces the prior cache.
    """
    global _baseline_candidates, _baseline_openai_tools

    from ..pnd.models import (
        CandidateCapability,
        ToolCandidate,
        candidates_to_openai_tool_schemas,
    )

    manifests_dir = Path(emerge_tools_dir) / "manifests"
    if not manifests_dir.exists():
        logger.warning(
            "platform_mcp_baseline: manifests dir not found at %s — baseline will be empty",
            manifests_dir,
        )
        return

    candidates: list[ToolCandidate] = []

    for yaml_path in sorted(manifests_dir.glob("*.yaml")):
        try:
            manifest = yaml.safe_load(yaml_path.read_text())
        except Exception:
            logger.exception(
                "platform_mcp_baseline: failed to parse %s — skipping", yaml_path.name
            )
            continue

        if (manifest.get("protocol") or {}).get("type", "").lower() != "mcp":
            continue

        tools_list = (manifest.get("capabilities") or {}).get("tools") or []
        if not tools_list:
            continue

        missing_keys = _missing_platform_env_keys(manifest)
        if missing_keys:
            logger.debug(
                "platform_mcp_baseline: skipping %s — missing env key(s): %s",
                yaml_path.name,
                ", ".join(missing_keys),
            )
            continue

        identity = manifest.get("identity") or {}
        agent_id = identity.get("id", yaml_path.stem)
        agent_name = identity.get("name", agent_id)
        agent_description = identity.get("description", "")

        capabilities = [
            CandidateCapability(
                capability_id=tool["name"],
                capability_type="TOOL",
                name=tool["name"],
                description=tool.get("description", ""),
                input_schema=tool.get("inputSchema"),
            )
            for tool in tools_list
        ]

        candidates.append(
            ToolCandidate(
                agent_id=agent_id,
                agent_name=agent_name,
                agent_description=agent_description,
                protocol_type="MCP",
                relevance_score=1.0,
                capabilities=capabilities,
                health_status="HEALTHY",
            )
        )

    _baseline_candidates = [c.model_dump(mode="json") for c in candidates]
    _baseline_openai_tools = candidates_to_openai_tool_schemas(candidates)

    # Seed MANIFEST_CACHE so PreFlight never needs to reach Registry for system
    # agents — without this, health checks fail when Registry is unreachable.
    from ..middleware.manifest_cache import MANIFEST_CACHE

    for yaml_path in sorted(manifests_dir.glob("*.yaml")):
        try:
            manifest = yaml.safe_load(yaml_path.read_text())
        except Exception:
            continue

        if (manifest.get("protocol") or {}).get("type", "").lower() != "mcp":
            continue

        tools_list = (manifest.get("capabilities") or {}).get("tools") or []
        if not tools_list:
            continue

        if _missing_platform_env_keys(manifest):
            continue

        identity = manifest.get("identity") or {}
        agent_id = identity.get("id", yaml_path.stem)

        normalized = {
            "agent_id": agent_id,
            "name": identity.get("name", agent_id),
            "description": identity.get("description", ""),
            "health_status": "HEALTHY",
            "health_endpoint": manifest.get("health_endpoint", ""),
            "transport": (manifest.get("protocol") or {}).get("transport", {}),
            "security": manifest.get("security", {}),
            "capabilities": [
                {
                    "capability_id": tool["name"],
                    "id": tool["name"],
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "input_schema": tool.get("inputSchema"),
                }
                for tool in tools_list
            ],
            "payment": manifest.get("payment", {}),
        }
        MANIFEST_CACHE.seed(agent_id, normalized)

    logger.info(
        "platform_mcp_baseline: loaded %d system MCP tool(s) from %d manifest(s)",
        sum(len(c.capabilities) for c in candidates),
        len(candidates),
    )


def get_baseline_candidates() -> list[dict[str, Any]]:
    """Return baseline ToolCandidate dicts (JSON-serialisable, shallow copy).

    Returns [] before load_baseline_from_manifests() is called — identical to
    prior default_state() behaviour, so tests that skip lifespan are unaffected.
    """
    return list(_baseline_candidates)


def get_baseline_openai_tools() -> list[dict[str, Any]]:
    """Return baseline OpenAI function schemas for all valid system MCP tools."""
    return list(_baseline_openai_tools)
