"""Thin HTTP client for SuperAgent → Registry service-to-service calls."""

from __future__ import annotations

import logging

import httpx
import yaml

logger = logging.getLogger(__name__)

REGISTER_PATH = "/api/v1/agents/register"


class RegistryClient:
    """Posts agent manifests to the Registry REST API.

    The Registry expects ``multipart/form-data`` with an ``emerge_yaml`` file
    (same as ``seed_agents.py`` / Gateway), not a JSON body.

    Path: ``POST /api/v1/agents/register`` (``app`` prefix ``/api`` + v1 ``/v1``
    + agents router ``/agents`` + ``/register``).

    ``X-Internal-Key`` is forwarded for future Registry middleware; user
    resolution still uses ``Authorization`` when auth is enabled. For local
    dev, run Registry with ``DISABLE_AUTH=true`` so ``verify_token`` resolves
    to ``dev_user`` without a Bearer token (see ``docker-compose.*.yml``).
    """

    def __init__(self, base_url: str, internal_api_key: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers: dict[str, str] = {}
        if internal_api_key:
            self._headers["X-Internal-Key"] = internal_api_key

    async def upsert_agent(self, manifest: dict) -> None:
        """Register an agent from a parsed manifest dict.

        Treats HTTP 409 (already registered) as success so boot-time seeding is
        idempotent. Raises on other non-success codes.
        """
        emerge_yaml_str = yaml.dump(
            manifest,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
        )
        files = {
            "emerge_yaml": (
                "emerge.yaml",
                emerge_yaml_str.encode("utf-8"),
                "application/x-yaml",
            ),
        }
        url = f"{self._base_url}{REGISTER_PATH}"
        # Capability harvest (MCP) can exceed a few seconds
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                url,
                files=files,
                headers=self._headers,
            )

        if resp.status_code == httpx.codes.CONFLICT:
            logger.debug(
                "Registry already has agent %s — skipping (409)",
                manifest.get("identity", {}).get("id", "unknown"),
            )
            return

        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError:
            logger.error(
                "Registry POST failed: %s %s — %s",
                resp.status_code,
                url,
                resp.text[:500],
            )
            raise

        logger.debug(
            "Registered agent %s (status=%d)",
            manifest.get("identity", {}).get("id", "unknown"),
            resp.status_code,
        )
