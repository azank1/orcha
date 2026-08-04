"""SystemToolRegistry — thread-safe singleton for built-in tool schemas."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


@dataclass
class SystemToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Awaitable[Any]]


class SystemToolRegistry:
    """Thread-safe registry of system tools."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._tools: dict[str, SystemToolSpec] = {}

    def register(self, spec: SystemToolSpec) -> None:
        with self._lock:
            self._tools[spec.name] = spec

    def has(self, name: str) -> bool:
        return name in self._tools

    def get_all_schemas(self) -> list[dict[str, Any]]:
        """Return OpenAI-compatible tool schema list for all registered tools."""
        with self._lock:
            return [
                {
                    "type": "function",
                    "function": {
                        "name": spec.name,
                        "description": spec.description,
                        "parameters": spec.parameters,
                    },
                }
                for spec in self._tools.values()
            ]

    async def call(self, name: str, args: dict[str, Any], state: dict[str, Any]) -> Any:
        spec = self._tools.get(name)
        if spec is None:
            raise KeyError(f"Unknown system tool: {name!r}")
        return await spec.handler(args, state)


# Module-level singleton (populated by register_all_system_tools() at boot)
SYSTEM_TOOL_REGISTRY = SystemToolRegistry()


def register_all_system_tools() -> None:
    """Register all built-in system tools into SYSTEM_TOOL_REGISTRY."""
    from .artifacts import register_artifact_tools
    from .attestation import register_attestation_tools
    from .checklist import register_checklist_tools
    from .enforcement import register_enforcement_tools
    from .mailer import register_mailer_tools
    from .memory import register_memory_tools
    from .utils import register_util_tools
    from .workflow import register_workflow_tools

    register_checklist_tools(SYSTEM_TOOL_REGISTRY)
    register_artifact_tools(SYSTEM_TOOL_REGISTRY)
    register_workflow_tools(SYSTEM_TOOL_REGISTRY)
    register_memory_tools(SYSTEM_TOOL_REGISTRY)
    register_util_tools(SYSTEM_TOOL_REGISTRY)
    register_enforcement_tools(SYSTEM_TOOL_REGISTRY)
    register_attestation_tools(SYSTEM_TOOL_REGISTRY)
    register_mailer_tools(SYSTEM_TOOL_REGISTRY)  # gated on SANDBOX_MAILER=true
