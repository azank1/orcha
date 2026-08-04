"""Version management service for agent manifests."""

import json
from datetime import UTC, datetime
from typing import Any


class VersionManager:
    """Service for managing agent version history."""

    @staticmethod
    def create_manifest_snapshot(
        agent_data: dict[str, Any],
        capabilities: list,
        security: dict[str, Any],
        payment: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """
        Create a full snapshot of the agent manifest for versioning.

        Args:
            agent_data: Core agent information
            capabilities: List of capabilities
            security: Security configuration
            payment: Payment configuration

        Returns:
            Complete manifest snapshot as dict
        """
        return {
            "identity": {
                "id": agent_data.get("id"),
                "name": agent_data.get("name"),
                "version": agent_data.get("version"),
                "description": agent_data.get("description"),
                "tags": agent_data.get("tags", []),
            },
            "protocol": {
                "type": agent_data.get("protocol_type"),
                "version": agent_data.get("protocol_version"),
            },
            "capabilities": capabilities,
            "security": security,
            "payment": payment,
            "snapshot_at": datetime.now(UTC).isoformat(),
        }

    @staticmethod
    def generate_change_summary(
        previous_snapshot: dict[str, Any] | None, current_snapshot: dict[str, Any]
    ) -> str:
        """
        Generate a human-readable summary of changes between versions.

        Args:
            previous_snapshot: Previous version snapshot (None if first version)
            current_snapshot: Current version snapshot

        Returns:
            Change summary string
        """
        if not previous_snapshot:
            return "Initial version"

        changes = []

        # Check capability changes
        prev_caps = previous_snapshot.get("capabilities", [])
        curr_caps = current_snapshot.get("capabilities", [])

        prev_cap_ids = {cap["id"] for cap in prev_caps}
        curr_cap_ids = {cap["id"] for cap in curr_caps}

        added = curr_cap_ids - prev_cap_ids
        removed = prev_cap_ids - curr_cap_ids

        if added:
            changes.append(f"Added {len(added)} capability(ies)")
        if removed:
            changes.append(f"Removed {len(removed)} capability(ies)")

        # Check protocol version change
        if previous_snapshot.get("protocol", {}).get("version") != current_snapshot.get(
            "protocol", {}
        ).get("version"):
            changes.append("Updated protocol version")

        # Check security changes
        prev_security = json.dumps(
            previous_snapshot.get("security", {}), sort_keys=True
        )
        curr_security = json.dumps(current_snapshot.get("security", {}), sort_keys=True)
        if prev_security != curr_security:
            changes.append("Updated security configuration")

        # Check payment changes
        prev_payment = json.dumps(previous_snapshot.get("payment", {}), sort_keys=True)
        curr_payment = json.dumps(current_snapshot.get("payment", {}), sort_keys=True)
        if prev_payment != curr_payment:
            changes.append("Updated payment configuration")

        if not changes:
            return "No significant changes detected"

        return "; ".join(changes)

    @staticmethod
    def compare_versions(version1: str, version2: str) -> int:
        """
        Compare two semantic versions.

        Args:
            version1: First version (e.g., "1.0.0")
            version2: Second version (e.g., "1.1.0")

        Returns:
            -1 if version1 < version2
             0 if version1 == version2
             1 if version1 > version2
        """
        v1_parts = [int(x) for x in version1.split(".")]
        v2_parts = [int(x) for x in version2.split(".")]

        for i in range(3):
            if v1_parts[i] < v2_parts[i]:
                return -1
            if v1_parts[i] > v2_parts[i]:
                return 1

        return 0
