"""Protocol adapters for agent capability harvesting."""

from .a2a import A2AAdapter
from .base import BaseAdapter, CapabilityData, HarvestResult
from .mcp import MCPAdapter

__all__ = [
    "BaseAdapter",
    "CapabilityData",
    "HarvestResult",
    "MCPAdapter",
    "A2AAdapter",
]
