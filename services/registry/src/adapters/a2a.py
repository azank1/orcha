"""A2A (Agent-to-Agent) protocol adapter implementation."""

import asyncio
import logging
from typing import Any

import httpx

from .base import BaseAdapter, CapabilityData, HarvestResult

logger = logging.getLogger(__name__)


def _a2a_schema_supported(agent_card: dict[str, Any]) -> bool:
    """
    Accept common Agent Card variants.

    Many agents omit ``schemaVersion`` entirely; if ``skills`` is present we still
    harvest (lenient). Numeric ``1`` / ``1.0`` from JSON is also accepted.
    """
    raw = agent_card.get("schemaVersion")
    if raw is None:
        raw = agent_card.get("schema_version")
    if raw is None:
        if agent_card.get("skills"):
            logger.warning(
                "A2A Agent Card has skills but no schemaVersion — assuming v1.0"
            )
            return True
        return False
    if isinstance(raw, bool):
        return False
    if isinstance(raw, (int, float)):
        return abs(float(raw) - 1.0) < 1e-9
    s = str(raw).strip().lower()
    return s in ("1.0", "1", "v1.0", "v1")


class A2AAdapter(BaseAdapter):
    """
    Adapter for A2A v1 protocol agents.

    Key Points:
    - authSchemes is TOP-LEVEL (not per-skill)
    - All skills use the same auth mechanism
    - Client chooses ONE scheme from authSchemes array
    """

    def __init__(
        self,
        endpoint: str,
        agent_card_json: dict | None = None,  # Pre-parsed from emerge.yaml
        timeout: int = 10,
        max_retries: int = 3,
    ):
        """
        Initialize A2A adapter.

        Args:
            endpoint: Base URL (e.g., https://agent.example.com)
            agent_card_json: Optional pre-parsed Agent Card
            timeout: Request timeout in seconds
            max_retries: Number of retry attempts
        """
        super().__init__(endpoint, timeout, max_retries)
        self.agent_card_json = agent_card_json

    async def harvest(self) -> HarvestResult:
        """
        Harvest A2A agent capabilities from Agent Card.

        Process:
        1. Fetch Agent Card (or use pre-parsed)
        2. Extract agent-level authSchemes
        3. Parse skills[] (no auth info here)
        4. Return normalized capabilities with agent-level metadata
        """
        try:
            # Fetch or use pre-parsed Agent Card
            agent_card = await self._get_agent_card()

            if not _a2a_schema_supported(agent_card):
                raw = agent_card.get("schemaVersion", agent_card.get("schema_version"))
                return HarvestResult(
                    capabilities=[],
                    errors=[f"Unsupported or missing A2A schema version: {raw!r}"],
                )

            capabilities = []
            errors = []

            # Parse skills (map to tools in universal format)
            for skill in agent_card.get("skills", []):
                try:
                    cap = CapabilityData(
                        type="tool",
                        id=skill["id"],
                        name=skill["name"],
                        description=skill.get("description", ""),
                        input_schema=skill.get("input_schema"),
                        output_schema=skill.get("output_schema"),
                    )
                    capabilities.append(cap)
                except KeyError as e:
                    errors.append(f"Invalid skill: missing field {e}")

            # Store agent-level auth schemes in metadata
            # These apply to ALL skills, not per-capability
            prov = agent_card.get("provider")
            harvest_metadata: dict[str, Any] = {
                "agent_auth_schemes": agent_card.get("authSchemes", []),
                "agent_name": agent_card.get("name"),
                "agent_description": agent_card.get("description"),
                "agent_url": agent_card.get("url"),
                "tags": agent_card.get("tags", []),
                "capabilities_meta": agent_card.get("capabilities", {}),
            }
            if isinstance(prov, str) and prov.strip():
                harvest_metadata["provider"] = prov.strip()

            return HarvestResult(
                capabilities=capabilities, errors=errors, metadata=harvest_metadata
            )

        except Exception as e:
            raise ConnectionError(f"Failed to harvest A2A agent: {str(e)}") from e

    async def _get_agent_card(self) -> dict[str, Any]:
        """Fetch Agent Card with retry logic."""
        # If pre-parsed from emerge.yaml, use that
        if self.agent_card_json:
            return self.agent_card_json

        # Otherwise, fetch from /.well-known/agent.json
        card_url = f"{self.endpoint.rstrip('/')}/.well-known/agent.json"

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        card_url,
                        timeout=self.timeout,
                        follow_redirects=True,
                    )
                    response.raise_for_status()
                    return response.json()

            except httpx.HTTPError as e:
                if attempt == self.max_retries - 1:
                    raise ConnectionError(
                        f"Failed to fetch Agent Card after {self.max_retries} attempts: {e}"
                    ) from e

                # Exponential backoff: 1s, 2s, 4s
                await asyncio.sleep(2**attempt)

        raise ConnectionError("Failed to fetch Agent Card")

    async def health_check(self) -> bool:
        """Check if Agent Card is accessible."""
        try:
            card_url = f"{self.endpoint.rstrip('/')}/.well-known/agent.json"

            async with httpx.AsyncClient() as client:
                response = await client.get(card_url, timeout=5, follow_redirects=True)
                return response.status_code == 200

        except Exception:
            return False
