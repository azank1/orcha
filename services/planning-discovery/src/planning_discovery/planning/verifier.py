"""Pre-flight capability verification.

Verifies that all agents and capabilities in the plan are
still healthy and available before sending to Runtime.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Protocol

from planning_discovery.schemas.internal import (
    ValidationIssue,
    ValidationSeverity,
    VerificationResult,
)

logger = logging.getLogger(__name__)


class RegistryClient(Protocol):
    """Protocol for fetching agent info from the Registry service."""

    async def get_agent(self, agent_id: str) -> dict[str, Any] | None:
        """Fetch agent manifest by ID. Returns None if not found."""
        ...

    async def check_agent_health(self, agent_id: str) -> str:
        """Check agent health status. Returns 'HEALTHY', 'UNHEALTHY', or 'UNKNOWN'."""
        ...


class MockRegistryClient:
    """Mock registry client for testing and offline development."""

    def __init__(self, agents: dict[str, dict[str, Any]] | None = None):
        self.agents = agents or {}

    async def get_agent(self, agent_id: str) -> dict[str, Any] | None:
        return self.agents.get(agent_id)

    async def check_agent_health(self, agent_id: str) -> str:
        agent = self.agents.get(agent_id)
        if not agent:
            return "UNKNOWN"
        return agent.get("health_status", "HEALTHY")


class Verifier:
    """Pre-flight verification of a workflow plan.

    Checks:
    - All agents exist in registry
    - All agents are HEALTHY (not UNHEALTHY/UNKNOWN)
    - All capabilities still exist on the agent
    """

    def __init__(self, registry: RegistryClient):
        self.registry = registry

    async def verify_dict(self, workflow_dag: dict[str, Any]) -> VerificationResult:
        """Run pre-flight checks on a workflow DAG dict.

        Works with the raw dict representation (post-pipeline,
        before WorkflowManifest hydration).

        Returns:
            VerificationResult indicating if the plan is executable.
        """
        t0 = time.monotonic()
        issues: list[ValidationIssue] = []

        nodes = workflow_dag.get("nodes", [])

        # Collect unique agent IDs (skip placeholders)
        agent_ids = {
            n.get("agent_id", "")
            for n in nodes
            if n.get("agent_id") and n["agent_id"] not in ("", "subgraph", "unresolved")
        }

        for agent_id in agent_ids:
            agent_issues = await self._verify_agent(agent_id, nodes)
            issues.extend(agent_issues)

        errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        executable = len(errors) == 0

        latency_ms = (time.monotonic() - t0) * 1000
        logger.info(
            "verifier_complete — executable=%s agents_checked=%d errors=%d warnings=%d latency=%.0fms",
            executable,
            len(agent_ids),
            len(errors),
            len(issues) - len(errors),
            latency_ms,
        )

        return VerificationResult(executable=executable, issues=issues)

    async def _verify_agent(
        self,
        agent_id: str,
        nodes: list[dict[str, Any]],
    ) -> list[ValidationIssue]:
        """Verify a single agent's availability and capabilities."""
        issues: list[ValidationIssue] = []

        # Check agent exists
        agent = await self.registry.get_agent(agent_id)
        if not agent:
            issues.append(
                ValidationIssue(
                    rule="agent_existence",
                    severity=ValidationSeverity.ERROR,
                    message=f"Agent '{agent_id}' not found in registry",
                )
            )
            return issues

        # Check agent health
        health = await self.registry.check_agent_health(agent_id)
        if health == "UNHEALTHY":
            issues.append(
                ValidationIssue(
                    rule="agent_health",
                    severity=ValidationSeverity.ERROR,
                    message=f"Agent '{agent_id}' is UNHEALTHY",
                )
            )
        elif health == "UNKNOWN":
            issues.append(
                ValidationIssue(
                    rule="agent_health",
                    severity=ValidationSeverity.WARNING,
                    message=f"Agent '{agent_id}' health status is UNKNOWN",
                )
            )

        # Check capabilities still exist
        agent_capabilities = {
            c.get("capability_id") or c.get("name")
            for c in agent.get("capabilities", [])
        }

        for node in nodes:
            if node.get("agent_id") == agent_id:
                # In the new schema, capabilities are tracked differently
                node_cap = node.get("capability", {})
                if isinstance(node_cap, dict):
                    cap_id = node_cap.get("capability_id") or node_cap.get("name")
                    if cap_id and cap_id not in agent_capabilities:
                        issues.append(
                            ValidationIssue(
                                rule="capability_existence",
                                severity=ValidationSeverity.ERROR,
                                message=f"Capability '{cap_id}' no longer exists on agent '{agent_id}'",
                                node_id=node.get("id"),
                            )
                        )

        return issues
