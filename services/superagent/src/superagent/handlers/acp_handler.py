"""ACPHandler — stub mirroring A2AHandler interface for ACP protocol agents."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.runnables import RunnableConfig

from .a2a_handler import A2AHandler

logger = logging.getLogger(__name__)


class ACPHandler(A2AHandler):
    """
    ACP protocol handler.

    ACP (Agent Communication Protocol) shares the same task-based lifecycle
    as A2A.  This stub delegates to A2AHandler; protocol-specific divergences
    can be added here as the ACP spec matures.
    """

    async def send_task(
        self,
        agent_id: str,
        task: str,
        transport: dict[str, Any],
        state: dict[str, Any],
        config: RunnableConfig | None = None,
        call_id: str = "",
    ) -> Any:
        logger.debug("ACPHandler delegating to A2AHandler for agent %s", agent_id)
        return await super().send_task(
            agent_id,
            task,
            transport,
            state,
            config=config,
            call_id=call_id,
        )
