"""WorkflowTemplateStore — Postgres persistence via Prisma."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class WorkflowTemplateStore:
    """CRUD for workflow_templates table."""

    async def save(
        self,
        user_id: str,
        name: str,
        goal_template: str,
        steps: list[dict[str, Any]],
        agents_used: list[str],
        description: str = "",
        parameters: dict[str, Any] | None = None,
        created_from_session: str | None = None,
    ) -> str:
        """Persist a workflow template. Returns the new record ID."""
        from src.generated_client import Prisma

        db = Prisma()
        await db.connect()
        try:
            record = await db.workflowtemplate.create(
                data={
                    "user_id": user_id,
                    "name": name,
                    "description": description,
                    "goal_template": goal_template,
                    "parameters": parameters or {},
                    "steps": steps,
                    "agents_used": agents_used,
                    "created_from_session": created_from_session,
                }
            )
            logger.info("Saved workflow template %s for user %s", record.id, user_id)
            return record.id
        finally:
            await db.disconnect()

    async def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        """Return all templates for a user."""
        from src.generated_client import Prisma

        db = Prisma()
        await db.connect()
        try:
            records = await db.workflowtemplate.find_many(
                where={"user_id": user_id},
                order={"created_at": "desc"},
            )
            return [
                {
                    "id": r.id,
                    "name": r.name,
                    "goal_template": r.goal_template,
                    "run_count": r.run_count,
                    "schedule_cron": r.schedule_cron,
                    "created_at": r.created_at.isoformat(),
                }
                for r in records
            ]
        finally:
            await db.disconnect()
