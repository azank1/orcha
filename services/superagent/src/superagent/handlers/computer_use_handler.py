"""ComputerUseHandler — open bridge interface for computer-use protocol agents.

Ships with a zero-dependency mock backend by default. External backends (e.g.
GodHands or any screenshot/action provider) plug in behind the ComputerUseBackend
ABC — set COMPUTER_USE_BACKEND to the fully-qualified class path to swap them in.

See docs/bridges.md for the contributor guide on building a production backend.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import Any

from langchain_core.runnables import RunnableConfig

from .base import AgentHandler

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Backend interface
# ---------------------------------------------------------------------------


class ComputerUseBackend(ABC):
    """Pluggable execution backend for computer-use actions.

    Implement this ABC to swap in a real screenshot/action provider.
    """

    @abstractmethod
    async def execute_action(
        self,
        action: str,
        target: str | None,
        extra: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a single computer-use action.

        Returns a dict with at minimum:
            "success": bool
            "result":  str  — human-readable outcome
        """
        ...


# ---------------------------------------------------------------------------
# Built-in open mock backend (default — zero closed dependencies)
# ---------------------------------------------------------------------------


class MockComputerUseBackend(ComputerUseBackend):
    """Open mock backend — simulates computer-use locally with no external calls.

    This is the default backend so the OSS stack runs end-to-end without any
    closed service dependency. It logs the action and returns a success stub.
    """

    async def execute_action(
        self,
        action: str,
        target: str | None,
        extra: dict[str, Any],
    ) -> dict[str, Any]:
        logger.info(
            "MockComputerUseBackend: action=%r target=%r extra=%r",
            action,
            target,
            extra,
        )
        return {
            "success": True,
            "result": f"[mock] {action} on {target or 'screen'} — OK",
            "backend": "mock",
            "action": action,
            "target": target,
        }


# ---------------------------------------------------------------------------
# Backend loader
# ---------------------------------------------------------------------------


def _load_backend() -> ComputerUseBackend:
    """Instantiate the configured backend (default: MockComputerUseBackend).

    Set COMPUTER_USE_BACKEND to a fully-qualified class path to swap backends:
        COMPUTER_USE_BACKEND=mypackage.backends.GodHandsBackend
    """
    backend_path = os.getenv("COMPUTER_USE_BACKEND", "").strip()
    if backend_path:
        try:
            module_path, cls_name = backend_path.rsplit(".", 1)
            import importlib

            mod = importlib.import_module(module_path)
            cls = getattr(mod, cls_name)
            instance = cls()
            if not isinstance(instance, ComputerUseBackend):
                raise TypeError(f"{cls_name} does not implement ComputerUseBackend")
            logger.info("ComputerUseHandler: loaded backend %s", backend_path)
            return instance
        except Exception:
            logger.warning(
                "ComputerUseHandler: failed to load backend %r — falling back to mock",
                backend_path,
                exc_info=True,
            )
    return MockComputerUseBackend()


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------


class ComputerUseHandler(AgentHandler):
    """Bridge handler for COMPUTER_USE protocol agents.

    Routes computer-use actions through a pluggable ComputerUseBackend.
    The open mock backend runs by default; set COMPUTER_USE_BACKEND to
    plug in any external provider (see docs/bridges.md).

    Expected args shape:
        action  — str  e.g. "screenshot", "click", "type", "navigate"
        target  — str | None  e.g. URL, element selector, coordinates
        + any action-specific fields
    """

    def __init__(self, auth_headers: dict[str, str]) -> None:
        super().__init__(auth_headers)
        self._backend: ComputerUseBackend = _load_backend()

    async def execute(
        self,
        args: dict[str, Any],
        transport: dict[str, Any],
        config: RunnableConfig | None = None,
        call_id: str = "",
    ) -> str:
        action = str(args.get("action", "screenshot"))
        target = args.get("target")
        extra = {k: v for k, v in args.items() if k not in ("action", "target")}

        await self.emit_event(
            config,
            {
                "type": "invocation_progress",
                "call_id": call_id,
                "message": f"computer-use: {action}"
                + (f" → {target}" if target else ""),
            },
        )

        outcome = await self._backend.execute_action(action, target, extra)
        return str(outcome.get("result", str(outcome)))
