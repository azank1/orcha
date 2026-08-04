"""Unit tests for DependencyRefiner (Stage 2c)."""

from __future__ import annotations

import pytest
from planning_discovery.planning.resolution.dependency_refiner import DependencyRefiner

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _task(task_id: str, inputs: dict | None = None, deps: list | None = None) -> dict:
    return {
        "id": task_id,
        "type": "agent_task",
        "description": f"Task {task_id}",
        "task": {"description": f"Task {task_id}", "inputs": inputs or {}},
        "inputs": inputs or {},
        "depends_on": deps or [],
        "data_dependencies": [],
    }


def _edge(source: str, target: str) -> dict:
    return {"from": source, "to": target}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestTransitiveReduction:
    """Tests for removing transitive edges via networkx."""

    @pytest.fixture
    def refiner(self) -> DependencyRefiner:
        return DependencyRefiner()

    def test_removes_transitive_edge(self, refiner: DependencyRefiner) -> None:
        """A→B, B→C, A→C should reduce to A→B, B→C (A→C is transitive)."""
        tasks = [_task("task_1"), _task("task_2"), _task("task_3")]
        edges = [
            _edge("task_1", "task_2"),
            _edge("task_2", "task_3"),
            _edge("task_1", "task_3"),  # Transitive — should be removed
        ]
        result = refiner.refine_dependencies(tasks, edges)
        edge_pairs = {(e["from"], e["to"]) for e in result["edges"]}
        assert ("task_1", "task_2") in edge_pairs
        assert ("task_2", "task_3") in edge_pairs
        assert ("task_1", "task_3") not in edge_pairs, (
            "Transitive edge should be removed"
        )

    def test_keeps_direct_edges(self, refiner: DependencyRefiner) -> None:
        """Simple A→B chain with no transitive edge: both edges kept."""
        tasks = [_task("task_1"), _task("task_2"), _task("task_3")]
        edges = [_edge("task_1", "task_2"), _edge("task_2", "task_3")]
        result = refiner.refine_dependencies(tasks, edges)
        assert len(result["edges"]) == 2

    def test_parallel_tasks_no_edges(self, refiner: DependencyRefiner) -> None:
        """Truly independent tasks produce zero edges."""
        tasks = [_task("task_1"), _task("task_2"), _task("task_3")]
        result = refiner.refine_dependencies(tasks, [])
        assert result["edges"] == []

    def test_four_task_chain(self, refiner: DependencyRefiner) -> None:
        """A→B→C→D with all transitive shortcuts reduces to just A→B→C→D."""
        tasks = [_task(f"t{i}") for i in range(1, 5)]
        edges = [
            _edge("t1", "t2"),
            _edge("t2", "t3"),
            _edge("t3", "t4"),
            _edge("t1", "t3"),  # Transitive
            _edge("t1", "t4"),  # Transitive
            _edge("t2", "t4"),  # Transitive
        ]
        result = refiner.refine_dependencies(tasks, edges)
        edge_pairs = {(e["from"], e["to"]) for e in result["edges"]}
        assert len(edge_pairs) == 3
        assert ("t1", "t2") in edge_pairs
        assert ("t2", "t3") in edge_pairs
        assert ("t3", "t4") in edge_pairs

    def test_empty_tasks(self, refiner: DependencyRefiner) -> None:
        """Empty task list returns empty result."""
        result = refiner.refine_dependencies([], [])
        assert result["nodes"] == []
        assert result["edges"] == []


class TestDataDependencyExtraction:
    """Tests for _extract_data_dependencies."""

    @pytest.fixture
    def refiner(self) -> DependencyRefiner:
        return DependencyRefiner()

    def test_extracts_dollar_tasks_reference(self, refiner: DependencyRefiner) -> None:
        """$tasks.<id>.output.<field> in inputs is detected as a data dependency."""
        tasks = [
            _task("task_1"),
            _task(
                "task_2", inputs={"check_in_date": "$tasks.task_1.output.arrival_time"}
            ),
        ]
        deps = refiner._extract_data_dependencies(tasks)
        assert "task_1" in deps["task_2"]

    def test_no_reference_no_dependency(self, refiner: DependencyRefiner) -> None:
        """Literal input values produce no data dependency."""
        tasks = [
            _task("task_1"),
            _task("task_2", inputs={"destination": "Tokyo"}),
        ]
        deps = refiner._extract_data_dependencies(tasks)
        assert not deps["task_2"]

    def test_nested_reference_path(self, refiner: DependencyRefiner) -> None:
        """Deep $tasks references like $tasks.t1.output.flights[0].arrival_time are detected."""
        tasks = [
            _task("t1"),
            _task(
                "t2", inputs={"check_in": "$tasks.t1.output.flights[0].arrival_time"}
            ),
        ]
        deps = refiner._extract_data_dependencies(tasks)
        assert "t1" in deps["t2"]

    def test_task_descriptor_inputs_scanned(self, refiner: DependencyRefiner) -> None:
        """Data references inside task.inputs (post-IO resolution) are also detected."""
        tasks = [
            _task("task_1"),
            {
                "id": "task_2",
                "type": "agent_task",
                "task": {"inputs": {"amount": "$tasks.task_1.output.total_cost"}},
                "inputs": {},
                "depends_on": [],
                "data_dependencies": [],
            },
        ]
        deps = refiner._extract_data_dependencies(tasks)
        assert "task_1" in deps["task_2"]


class TestSequentialDependencyExtraction:
    """Tests for _extract_sequential_dependencies."""

    @pytest.fixture
    def refiner(self) -> DependencyRefiner:
        return DependencyRefiner()

    def test_standard_from_to_edges(self, refiner: DependencyRefiner) -> None:
        tasks = [_task("t1"), _task("t2")]
        edges = [{"from": "t1", "to": "t2"}]
        seq_deps = refiner._extract_sequential_dependencies(tasks, edges)
        assert "t1" in seq_deps.get("t2", set())

    def test_source_target_edges_normalised(self, refiner: DependencyRefiner) -> None:
        """Edges using source/target keys are also accepted."""
        tasks = [_task("t1"), _task("t2")]
        edges = [{"source": "t1", "target": "t2"}]
        seq_deps = refiner._extract_sequential_dependencies(tasks, edges)
        assert "t1" in seq_deps.get("t2", set())

    def test_unknown_task_edge_ignored(self, refiner: DependencyRefiner) -> None:
        """Edges referencing tasks not in the current list are ignored."""
        tasks = [_task("t1")]
        edges = [{"from": "t1", "to": "ghost"}]
        seq_deps = refiner._extract_sequential_dependencies(tasks, edges)
        assert "ghost" not in seq_deps


class TestMergeAndReduce:
    """Tests for the merge step that combines data + sequential deps."""

    @pytest.fixture
    def refiner(self) -> DependencyRefiner:
        return DependencyRefiner()

    def test_data_dep_overrides_no_seq_dep(self, refiner: DependencyRefiner) -> None:
        """Data dependency alone creates an edge even without a sequential edge."""
        tasks = [_task("t1"), _task("t2")]
        task_map = {t["id"]: t for t in tasks}
        data_deps = {"t1": set(), "t2": {"t1"}}
        seq_deps: dict = {}
        edges = refiner._merge_and_reduce(data_deps, seq_deps, task_map)
        assert any(e["from"] == "t1" and e["to"] == "t2" for e in edges)
