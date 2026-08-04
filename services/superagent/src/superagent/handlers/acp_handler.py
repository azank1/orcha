"""ACPHandler — ACP compatibility alias, routed through the A2A handler."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.runnables import RunnableConfig

from .a2a_handler import A2AHandler

logger = logging.getLogger(__name__)


class ACPHandler(A2AHandler):
    """
    ACP compatibility handler.

    ACP manifests are accepted at the API/schema layer for compatibility and
    routed through the A2A handler at runtime — IBM's ACP merged into A2A
    upstream (August 2025), so ACP is not an independently maintained protocol
    here. This subclass exists so dispatch and logging can label ACP traffic.
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
