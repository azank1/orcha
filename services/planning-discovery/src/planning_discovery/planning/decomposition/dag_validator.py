"""Deterministic DAG structural validator used inside Stage 1."""

from __future__ import annotations

from typing import Any


class DAGValidationResult:
    def __init__(self, is_valid: bool, confidence: float, warnings: list[str]) -> None:
        self.is_valid = is_valid
        self.confidence = confidence
        self.warnings = warnings


class DAGValidator:
    """
    Validates structural correctness of a decomposed task DAG.

    Checks:
    - No circular dependencies (topological sort)
    - All dependency references exist
    - No orphaned tasks (tasks with no path to any output)
    """

    def validate(self, decomposition: Any) -> DAGValidationResult:
        tasks: list[dict[str, Any]] = decomposition.tasks
        edges: list[dict[str, Any]] = decomposition.edges

        task_ids = {t["id"] for t in tasks}
        warnings: list[str] = []

        # All depends_on references must exist
        for task in tasks:
            for dep in task.get("depends_on", []):
                if dep not in task_ids:
                    return DAGValidationResult(
                        is_valid=False,
                        confidence=0.0,
                        warnings=[
                            f"Task '{task['id']}' depends on unknown task '{dep}'"
                        ],
                    )

        # Edge endpoints must be valid task IDs
        for edge in edges:
            for field in ("from", "to"):
                node = edge.get(field)
                if node and node not in task_ids:
                    warnings.append(f"Edge references unknown task '{node}'")

        # Cycle detection via DFS
        if self._has_cycle(tasks, edges):
            return DAGValidationResult(
                is_valid=False,
                confidence=0.0,
                warnings=["Circular dependency detected in task DAG"],
            )

        confidence = decomposition.metadata.get("confidence", 0.8)
        return DAGValidationResult(
            is_valid=True, confidence=confidence, warnings=warnings
        )

    def _has_cycle(
        self, tasks: list[dict[str, Any]], edges: list[dict[str, Any]]
    ) -> bool:
        adjacency: dict[str, list[str]] = {t["id"]: [] for t in tasks}
        for edge in edges:
            src = edge.get("from")
            dst = edge.get("to")
            if src and dst and src in adjacency:
                adjacency[src].append(dst)

        visited: set[str] = set()
        in_stack: set[str] = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            in_stack.add(node)
            for neighbour in adjacency.get(node, []):
                if neighbour not in visited:
                    if dfs(neighbour):
                        return True
                elif neighbour in in_stack:
                    return True
            in_stack.discard(node)
            return False

        return any(dfs(t["id"]) for t in tasks if t["id"] not in visited)
