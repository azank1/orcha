"""Stage 2c — Dependency Refinement.

Cleans the task DAG by removing transitive edges and preserving only direct
data-flow dependencies.  Enables proper parallel execution of independent tasks.

Principles:
  1. Keep edges where task B's inputs explicitly reference task A's outputs
  2. Remove transitive edges: if A→B and B→C exist, remove A→C
  3. Preserve sequential dependencies from the decomposition where data flows
  4. Enable parallelisation for truly independent tasks (no shared data)
"""

from __future__ import annotations

import logging
from typing import Any

import networkx as nx

logger = logging.getLogger(__name__)


class DependencyRefiner:
    """
    Refines the workflow DAG to remove unnecessary dependency edges.

    Stateless — all methods are pure functions; no LLM calls required.
    """

    def refine_dependencies(
        self,
        tasks: list[dict[str, Any]],
        initial_edges: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Main entry point for dependency refinement.

        Args:
            tasks:         IO-resolved task list (each task may have ``data_dependencies``
                           and ``task.inputs`` with ``$tasks.*`` references).
            initial_edges: Raw edges from Stage 1 decomposition
                           (using ``from``/``to`` or ``source``/``target`` keys).

        Returns:
            ``{"nodes": tasks, "edges": refined_edges}`` where edges use
            ``{"from": str, "to": str, "condition": str | None}`` format.
        """
        if not tasks:
            return {"nodes": tasks, "edges": []}

        task_map: dict[str, dict[str, Any]] = {t["id"]: t for t in tasks}

        # Step 1: Data dependencies extracted from $tasks.* input references
        data_deps = self._extract_data_dependencies(tasks)
        logger.debug("[DependencyRefiner] data_deps: %s", data_deps)

        # Step 2: Sequential dependencies from the initial decomposition edges
        seq_deps = self._extract_sequential_dependencies(tasks, initial_edges)
        logger.debug("[DependencyRefiner] seq_deps (from decomposition): %s", seq_deps)

        # Step 3: Merge both sets and remove transitive edges
        refined_edges = self._merge_and_reduce(data_deps, seq_deps, task_map)
        logger.info(
            "[DependencyRefiner] refined %d initial edges to %d direct edges",
            len(initial_edges),
            len(refined_edges),
        )

        return {"nodes": tasks, "edges": refined_edges}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_data_dependencies(
        self,
        tasks: list[dict[str, Any]],
    ) -> dict[str, set[str]]:
        """
        Extract explicit data dependencies by scanning ``$tasks.<id>.output.*`` references.

        Also reads the ``data_dependencies`` list set by ``IOResolver._resolve_inputs()``.

        Returns:
            ``{task_id: {set of task_ids it depends on}}``
        """
        dependencies: dict[str, set[str]] = {}

        for task in tasks:
            task_id = task["id"]
            task_deps: set[str] = set()

            # Scan inputs inside the ``task`` descriptor (post-IO resolution)
            task_descriptor = task.get("task", {})
            task_inputs: dict[str, Any] = task_descriptor.get("inputs", {})
            for input_value in task_inputs.values():
                if isinstance(input_value, str) and input_value.startswith("$tasks."):
                    # Format: $tasks.<task_id>.output.<field_path>
                    parts = input_value.split(".")
                    if len(parts) >= 2:
                        referenced_task_id = parts[1]
                        if referenced_task_id in {t["id"] for t in tasks}:
                            task_deps.add(referenced_task_id)

            # Also check top-level inputs dict (pre-IO resolution tasks)
            top_inputs: dict[str, Any] = task.get("inputs", {})
            for input_value in top_inputs.values():
                if isinstance(input_value, str) and input_value.startswith("$tasks."):
                    parts = input_value.split(".")
                    if len(parts) >= 2:
                        referenced_task_id = parts[1]
                        if referenced_task_id in {t["id"] for t in tasks}:
                            task_deps.add(referenced_task_id)

            # Explicit data_dependencies set by IOResolver
            for dep_id in task.get("data_dependencies", []):
                if dep_id in {t["id"] for t in tasks}:
                    task_deps.add(dep_id)

            dependencies[task_id] = task_deps

        return dependencies

    def _extract_sequential_dependencies(
        self,
        tasks: list[dict[str, Any]],
        initial_edges: list[dict[str, Any]],
    ) -> dict[str, set[str]]:
        """
        Convert the initial decomposition edges to a dependency map.

        Only preserves edges that connect nodes present in the current task list.
        Supports both ``from``/``to`` and ``source``/``target`` edge formats.

        Returns:
            ``{target_task_id: {set of source_task_ids}}``
        """
        valid_ids = {t["id"] for t in tasks}
        dependencies: dict[str, set[str]] = {}

        for edge in initial_edges:
            source = edge.get("from") or edge.get("source", "")
            target = edge.get("to") or edge.get("target", "")
            if source in valid_ids and target in valid_ids:
                if target not in dependencies:
                    dependencies[target] = set()
                dependencies[target].add(source)

        return dependencies

    def _merge_and_reduce(
        self,
        data_deps: dict[str, set[str]],
        seq_deps: dict[str, set[str]],
        task_map: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Merge data and sequential dependencies then remove transitive edges.

        Uses NetworkX transitive_reduction to keep only direct dependencies.
        """
        # Merge both dependency sets per target node
        all_deps: dict[str, set[str]] = {}
        for task_id in task_map:
            merged: set[str] = set()
            merged.update(data_deps.get(task_id, set()))
            merged.update(seq_deps.get(task_id, set()))
            all_deps[task_id] = merged

        # Build directed graph: edge A→B means B depends on A
        G: nx.DiGraph = nx.DiGraph()
        for task_id in task_map:
            G.add_node(task_id)

        for task_id, deps in all_deps.items():
            for dep in deps:
                # dep → task_id (dep must complete before task_id runs)
                G.add_edge(dep, task_id)

        # Remove transitive edges: if A→B and B→C exist, remove A→C
        try:
            reduced_graph = nx.transitive_reduction(G)
        except nx.NetworkXError as exc:
            logger.warning(
                "Transitive reduction failed (cycle detected?): %s — using original edges",
                exc,
            )
            reduced_graph = G

        edges: list[dict[str, Any]] = []
        for source, target in reduced_graph.edges():
            # Find any condition from original initial_edges
            edges.append(
                {
                    "from": source,
                    "to": target,
                    "condition": None,
                }
            )

        return edges

    def _transitive_reduction(
        self,
        G: nx.DiGraph,
    ) -> list[tuple[str, str]]:
        """Remove transitive edges from DAG using NetworkX."""
        reduced = nx.transitive_reduction(G)
        return list(reduced.edges())
