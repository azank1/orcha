"""Background health monitoring service using APScheduler."""

import asyncio
from datetime import UTC, datetime

import grpc
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from common.database.src.generated_client import Prisma
from google.protobuf.timestamp_pb2 import Timestamp

from common.proto.src import registry_pb2, registry_pb2_grpc

from ..config import settings
from ..services.health_check import HealthCheckService


class HealthMonitor:
    """Background service for monitoring agent health using APScheduler."""

    def __init__(self, db: Prisma, grpc_channel: grpc.aio.Channel | None = None):
        """
        Initialize health monitor.

        Args:
            db: Prisma database client
            grpc_channel: Optional gRPC channel for calling UpdateAgentHealth
        """
        self.db = db
        self.grpc_channel = grpc_channel
        self.health_service = HealthCheckService(timeout=5)
        self.scheduler = AsyncIOScheduler()

    async def start(self):
        """Start the health monitoring scheduler."""
        # Add job to scheduler
        self.scheduler.add_job(
            self._check_all_agents,
            trigger=IntervalTrigger(seconds=settings.health_check_interval),
            id="health_check_job",
            name="Agent Health Check",
            replace_existing=True,
        )

        # Start scheduler
        self.scheduler.start()
        print(f"✓ Health monitor started (interval: {settings.health_check_interval}s)")

    async def stop(self):
        """Stop the health monitoring scheduler."""
        self.scheduler.shutdown(wait=True)
        print("✓ Health monitor stopped")

    async def _check_all_agents(self):
        """Check health of all active agents."""
        try:
            # Get all active agents with their transport type.
            # STDIO agents are spawned on demand — no HTTP service to probe.
            agents_raw = await self.db.agent.find_many(
                where={"is_active": True},
                include={"transport": True},
            )
            # Skip STDIO agents — they have no HTTP health endpoint.
            agents = [
                a
                for a in agents_raw
                if not (a.transport and a.transport.type.upper() == "STDIO")
            ]

            print(
                f"[{datetime.now(UTC).isoformat()}] Checking health of {len(agents)} agents..."
            )

            # Check each agent in parallel
            tasks = [self._check_agent_health(agent) for agent in agents]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Count results
            healthy = sum(1 for r in results if r is True)
            unhealthy = sum(1 for r in results if r is False)
            errors = sum(1 for r in results if isinstance(r, Exception))

            print(
                f"[{datetime.now(UTC).isoformat()}] Health check complete: {healthy} healthy, {unhealthy} unhealthy, {errors} errors"
            )

        except Exception as e:
            print(f"✗ Health monitor error: {e}")

    async def _check_agent_health(self, agent) -> bool:
        """
        Check health of a single agent.

        Args:
            agent: Agent record from database

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Perform health check
            is_healthy, error_message = await self.health_service.check_agent_health(
                agent.health_endpoint
            )

            # Determine status
            new_failures = 0 if is_healthy else agent.health_failures + 1
            status = self.health_service.get_health_status(
                is_healthy, new_failures, settings.max_health_failures
            )

            # Update via gRPC if channel available, otherwise update directly
            if self.grpc_channel:
                await self._update_health_via_grpc(agent.id, status, error_message)
            else:
                await self._update_health_directly(
                    agent.id, status, new_failures, error_message
                )

            return is_healthy

        except Exception as e:
            print(f"Error checking health for agent {agent.name}: {e}")
            return False

    async def _update_health_via_grpc(
        self, agent_id: str, status: str, error_message: str
    ):
        """
        Update agent health via gRPC call.

        Args:
            agent_id: Agent ID
            status: Health status
            error_message: Error message if unhealthy
        """
        try:
            stub = registry_pb2_grpc.RegistryServiceStub(self.grpc_channel)

            # Map status to proto enum
            status_map = {
                "HEALTHY": registry_pb2.HEALTH_STATUS_HEALTHY,
                "UNHEALTHY": registry_pb2.HEALTH_STATUS_UNHEALTHY,
                "UNKNOWN": registry_pb2.HEALTH_STATUS_UNKNOWN,
            }

            timestamp = Timestamp()
            timestamp.FromDatetime(datetime.now(UTC))

            request = registry_pb2.UpdateHealthRequest(
                agent_id=agent_id,
                status=status_map[status],
                last_error=error_message,
                checked_at=timestamp,
            )

            await stub.UpdateAgentHealth(request)

        except Exception as e:
            print(f"Failed to update health via gRPC: {e}")
            # Fall back to direct update
            await self._update_health_directly(agent_id, status, 0, error_message)

    async def _update_health_directly(
        self, agent_id: str, status: str, failures: int, error_message: str
    ):
        """
        Update agent health directly in database.

        Args:
            agent_id: Agent ID
            status: Health status
            failures: Failure count
            error_message: Error message if unhealthy
        """
        await self.db.agent.update(
            where={"id": agent_id},
            data={
                "health_status": status,
                "health_failures": failures,
                "last_health_check": datetime.now(UTC),
            },
        )
