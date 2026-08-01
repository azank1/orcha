"""WorkflowScheduler — cron-based execution of saved workflow templates.

This is a lightweight scheduler that runs inside the SuperAgent process.
For production, replace with Celery Beat or a dedicated scheduler service.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


class WorkflowScheduler:
    """Polls for due scheduled workflows and enqueues them for execution."""

    def __init__(self, poll_interval: int = 60) -> None:
        self._poll_interval = poll_interval
        self._task: asyncio.Task[None] | None = None
        self._running = False

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._loop(), name="workflow-scheduler")
        logger.info(
            "WorkflowScheduler started (poll_interval=%ds)", self._poll_interval
        )

    async def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        logger.info("WorkflowScheduler stopped")

    async def _loop(self) -> None:
        while self._running:
            try:
                await self._tick()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("WorkflowScheduler tick error")
            await asyncio.sleep(self._poll_interval)

    async def _tick(self) -> None:
        """Find due templates and trigger execution."""
        from src.generated_client import Prisma

        now = datetime.now(tz=UTC)
        db = Prisma()
        await db.connect()
        try:
            due = await db.workflowtemplate.find_many(
                where={
                    "schedule_enabled": True,
                    "next_run_at": {"lte": now},
                }
            )
            for template in due:
                logger.info(
                    "Triggering scheduled workflow %s (%s) for user %s",
                    template.id,
                    template.name,
                    template.user_id,
                )
                asyncio.create_task(
                    self._run_template(template),
                    name=f"workflow-{template.id}",
                )
        finally:
            await db.disconnect()

    async def _run_template(self, template: Any) -> None:
        """Execute a workflow template as a new SuperAgent session."""
        # TODO: create a session and inject the goal as the first user message
        logger.info("WorkflowScheduler: executing template %s (stub)", template.id)
