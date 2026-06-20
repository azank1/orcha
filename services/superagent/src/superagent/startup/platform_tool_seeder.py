"""PlatformToolSeeder — registers system MCP tools with the Registry at SuperAgent boot."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import yaml

from ..clients.registry_client import RegistryClient

logger = logging.getLogger(__name__)


class PlatformToolSeeder:
    """Reads emerge-tools/manifests/, validates platform_env secrets, registers with Registry.

    Boot behaviour (spec §3):
    - Loads all *.yaml from emerge_tools_dir/manifests/
    - For each manifest: checks every platform_env auth strategy key exists in
      ``os.environ`` (populate secrets via ``services/superagent/.env`` + Settings
      and ``main.lifespan`` ``setdefault`` before seeding)
    - If any key is missing: logs WARNING and skips that tool (does NOT fail boot)
    - If all keys present: POSTs to Registry ``POST /api/v1/agents/register`` via RegistryClient
    - Logs a summary: "Seeded N/M platform tools successfully"
    """

    def __init__(self, registry_client: RegistryClient, emerge_tools_dir: str) -> None:
        self._client = registry_client
        self._manifests_dir = Path(emerge_tools_dir) / "manifests"

    async def seed(self) -> None:
        if not self._manifests_dir.exists():
            logger.warning(
                "emerge-tools manifests dir not found at %s — skipping platform tool seeding",
                self._manifests_dir,
            )
            return

        yaml_files = sorted(self._manifests_dir.glob("*.yaml"))
        if not yaml_files:
            logger.warning("No manifest files found in %s", self._manifests_dir)
            return

        total = len(yaml_files)
        seeded = 0

        for yaml_path in yaml_files:
            try:
                manifest = yaml.safe_load(yaml_path.read_text())
            except Exception:
                logger.exception(
                    "Failed to parse manifest %s — skipping", yaml_path.name
                )
                continue

            missing_keys = self._missing_platform_env_keys(manifest)
            if missing_keys:
                logger.warning(
                    "Skipping %s — missing platform_env key(s): %s",
                    yaml_path.name,
                    ", ".join(missing_keys),
                )
                continue

            try:
                await self._client.upsert_agent(manifest)
                seeded += 1
                logger.debug("Seeded platform tool: %s", yaml_path.name)
            except Exception:
                logger.exception(
                    "Failed to register platform tool %s — skipping", yaml_path.name
                )

        logger.info("Seeded %d/%d platform tools successfully", seeded, total)

    @staticmethod
    def _missing_platform_env_keys(manifest: dict) -> list[str]:
        """Return env keys declared as platform_env but absent from os.environ."""
        missing: list[str] = []
        strategies = manifest.get("security", {}).get("auth_strategies", []) or []
        for strategy in strategies:
            if strategy.get("type") == "platform_env":
                key = (strategy.get("config") or {}).get("env_key", "")
                if key and key not in os.environ:
                    missing.append(key)
        return missing
