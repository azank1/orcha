"""Tier 1 — Deterministic structural validation of workflow DAGs.

Checks performed (all O(n)):
  - Required top-level fields present
  - Every node has the mandatory fields for its type
  - Every edge source/target references a declared node
  - Graph is a DAG (no cycles — DFS-based)
  - Entry node declared, exists, and has no in-edges
  - Dependency list consistency (declared deps == in-edges)
"""

from __future__ import annotations

import logging
from typing import Any

from ...schemas.internal import ValidationResult

logger = logging.getLogger(__name__)

# Fields that every workflow manifest must have
_REQUIRED_TOP_LEVEL = {"nodes", "edges", "entry_node_id", "metadata"}

# Per-type required node fields (beyond the common ones)
_STANDARD_NODE_REQUIRED = {"id", "type", "agent_id"}
_ROUTER_NODE_REQUIRED = {"id", "type", "routing_key", "branches"}
_SYSTEM_TOOL_NODE_REQUIRED = {"id", "type", "tool_name"}

_VALID_NODE_TYPES = {"standard", "router", "system_tool"}


class DeterministicValidator:
    """
    Performs fast, deterministic (rule-based) validation of a workflow DAG dict.

    Returns a ``ValidationResult`` — callers should short-circuit if
    ``is_valid`` is ``False``.
    """

    def validate(self, workflow_dag: dict[str, Any]) -> ValidationResult:
        issues: list[str] = []

        # 1. Top-level structure
        missing = _REQUIRED_TOP_LEVEL - set(workflow_dag.keys())
        if missing:
            issues.append(f"Missing required top-level fields: {sorted(missing)}")
            # Can't continue without nodes/edges
            return ValidationResult(is_valid=False, issues=issues, tier="deterministic")

        nodes: list[dict[str, Any]] = workflow_dag.get("nodes") or []
        edges: list[dict[str, Any]] = workflow_dag.get("edges") or []
        entry_node_id: str | None = workflow_dag.get("entry_node_id")

        if not nodes:
            issues.append("Workflow must have at least one node")
            return ValidationResult(is_valid=False, issues=issues, tier="deterministic")

        # 2. Build node index and validate per-node fields
        node_ids: set[str] = set()
        for node in nodes:
            node_id = node.get("id", "")
            if not node_id:
                issues.append("Found a node with a missing or empty 'id'")
                continue
            if node_id in node_ids:
                issues.append(f"Duplicate node id: '{node_id}'")
            node_ids.add(node_id)
            issues.extend(self._validate_node_fields(node))

        # 3. Validate edges and build adjacency / in-degree structures
        in_edges: dict[str, set[str]] = {nid: set() for nid in node_ids}
        out_edges: dict[str, set[str]] = {nid: set() for nid in node_ids}

        for edge in edges:
            src = edge.get("source", "")
            tgt = edge.get("target", "")

            if not src or not tgt:
                issues.append(f"Edge missing source or target: {edge}")
                continue
            if src not in node_ids:
                issues.append(f"Edge source '{src}' does not reference a declared node")
                continue
            if tgt not in node_ids:
                issues.append(f"Edge target '{tgt}' does not reference a declared node")
                continue

            out_edges[src].add(tgt)
            in_edges[tgt].add(src)

        # 4. Entry node checks
        if entry_node_id not in node_ids:
            issues.append(
                f"entry_node_id '{entry_node_id}' does not reference a declared node"
            )
        elif in_edges.get(entry_node_id):
            issues.append(f"Entry node '{entry_node_id}' must not have any in-edges")

        # 5. Cycle detection (DFS)
        if self._has_cycle(node_ids, out_edges):
            issues.append("Workflow DAG contains a cycle — execution would deadlock")

        # 6. Dependency list consistency
        for node in nodes:
            node_id = node.get("id", "")
            if not node_id:
                continue
            declared_deps: list[str] = node.get("dependencies", []) or []
            actual_in = in_edges.get(node_id, set())
            declared_set = set(declared_deps)
            if declared_set != actual_in:
                extra = declared_set - actual_in
                missing_dep = actual_in - declared_set
                if extra:
                    issues.append(
                        f"Node '{node_id}': dependencies {sorted(extra)} declared but no matching in-edge"
                    )
                if missing_dep:
                    issues.append(
                        f"Node '{node_id}': in-edges from {sorted(missing_dep)} but not listed in dependencies"
                    )

        is_valid = len(issues) == 0
        logger.debug(
            "Deterministic validation %s — %d issue(s)",
            "passed" if is_valid else "FAILED",
            len(issues),
        )
        return ValidationResult(is_valid=is_valid, issues=issues, tier="deterministic")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _validate_node_fields(self, node: dict[str, Any]) -> list[str]:
        issues: list[str] = []
        node_id = node.get("id", "<unknown>")
        node_type = node.get("type", "")

        if node_type not in _VALID_NODE_TYPES:
            issues.append(
                f"Node '{node_id}': invalid type '{node_type}' — must be one of {sorted(_VALID_NODE_TYPES)}"
            )
            return issues

        if node_type == "standard":
            missing = _STANDARD_NODE_REQUIRED - set(node.keys())
        elif node_type == "router":
            missing = _ROUTER_NODE_REQUIRED - set(node.keys())
            if "branches" in node and not isinstance(node["branches"], list):
                issues.append(f"Router node '{node_id}': 'branches' must be a list")
        else:  # system_tool
            missing = _SYSTEM_TOOL_NODE_REQUIRED - set(node.keys())

        if missing:
            issues.append(
                f"Node '{node_id}' (type={node_type}) missing required fields: {sorted(missing)}"
            )

        return issues

    @staticmethod
    def _has_cycle(node_ids: set[str], out_edges: dict[str, set[str]]) -> bool:
        """DFS-based cycle detection — returns True if a cycle exists."""
        WHITE, GREY, BLACK = 0, 1, 2
        color: dict[str, int] = dict.fromkeys(node_ids, WHITE)

        def dfs(node: str) -> bool:
            color[node] = GREY
            for neighbour in out_edges.get(node, set()):
                if color[neighbour] == GREY:
                    return True
                if color[neighbour] == WHITE and dfs(neighbour):
                    return True
            color[node] = BLACK
            return False

        return any(dfs(node) for node in node_ids if color[node] == WHITE)
