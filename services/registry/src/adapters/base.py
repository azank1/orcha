"""Base adapter interface for protocol-specific harvesting."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class CapabilityData(BaseModel):
    """Normalized capability structure."""

    type: str  # "tool", "resource", "prompt"
    id: str
    name: str
    description: str
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    uri_template: str | None = None
    mime_type: str | None = None
    arguments: list[dict[str, Any]] | None = None


class HarvestResult(BaseModel):
    """Result of harvesting operation."""

    capabilities: list[CapabilityData]
    errors: list[str] = []
    metadata: dict[
        str, Any
    ] = {}  # Agent-level data (auth schemes, provider info, etc.)


class BaseAdapter(ABC):
    """Abstract base adapter for protocol-specific harvesting."""

    def __init__(self, endpoint: str, timeout: int = 10, max_retries: int = 3):
        self.endpoint = endpoint
        self.timeout = timeout
        self.max_retries = max_retries

    @abstractmethod
    async def harvest(self) -> HarvestResult:
        """
        Harvest capabilities from agent endpoint.

        Returns:
            HarvestResult with capabilities and any errors encountered.

        Raises:
            ConnectionError: If endpoint unreachable after retries.
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if agent endpoint is healthy.

        Returns:
            True if healthy, False otherwise.
        """
        pass
