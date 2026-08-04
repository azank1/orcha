"""Unit tests for DAG validation."""

from __future__ import annotations

import types

import pytest
from planning_discovery.planning.decomposition.dag_validator import DAGValidator

pytestmark = pytest.mark.unit


def _decomposition(tasks: list, edges: list, confidence: float = 0.9) -> object:
    """Build a simple namespace that mimics the decomposition object DAGValidator expects."""
    return types.SimpleNamespace(
        tasks=tasks,
        edges=edges,
        metadata={"confidence": confidence},
    )


class TestDAGValidator:
    """Tests for DAG validation logic."""

    @pytest.fixture
    def validator(self) -> DAGValidator:
        return DAGValidator()

    def test_valid_linear_dag(self, validator: DAGValidator) -> None:
        """Test validation of linear task chain."""
        decomp = _decomposition(
            tasks=[
                {"id": "task_1", "depends_on": []},
                {"id": "task_2", "depends_on": ["task_1"]},
                {"id": "task_3", "depends_on": ["task_2"]},
            ],
            edges=[
                {"from": "task_1", "to": "task_2"},
                {"from": "task_2", "to": "task_3"},
            ],
        )
        result = validator.validate(decomp)
        assert result.is_valid is True
        assert len(result.warnings) == 0

    def test_valid_parallel_dag(self, validator: DAGValidator) -> None:
        """Test validation with parallel branches."""
        decomp = _decomposition(
            tasks=[
                {"id": "task_1", "depends_on": []},
                {"id": "task_2", "depends_on": ["task_1"]},
                {"id": "task_3", "depends_on": ["task_1"]},
                {"id": "task_4", "depends_on": ["task_2", "task_3"]},
            ],
            edges=[
                {"from": "task_1", "to": "task_2"},
                {"from": "task_1", "to": "task_3"},
                {"from": "task_2", "to": "task_4"},
                {"from": "task_3", "to": "task_4"},
            ],
            confidence=0.85,
        )
        result = validator.validate(decomp)
        assert result.is_valid is True

    def test_circular_dependency_detection(self, validator: DAGValidator) -> None:
        """Test detection of circular dependencies."""
        decomp = _decomposition(
            tasks=[
                {"id": "task_1", "depends_on": ["task_3"]},
                {"id": "task_2", "depends_on": ["task_1"]},
                {"id": "task_3", "depends_on": ["task_2"]},
            ],
            edges=[
                {"from": "task_3", "to": "task_1"},
                {"from": "task_1", "to": "task_2"},
                {"from": "task_2", "to": "task_3"},
            ],
            confidence=0.5,
        )
        result = validator.validate(decomp)
        assert result.is_valid is False
        assert any(
            "circular" in w.lower() or "cycle" in w.lower() for w in result.warnings
        )

    def test_invalid_dependency_reference(self, validator: DAGValidator) -> None:
        """Test detection of references to non-existent tasks."""
        decomp = _decomposition(
            tasks=[
                {"id": "task_1", "depends_on": []},
                {"id": "task_2", "depends_on": ["task_999"]},
            ],
            edges=[{"from": "task_1", "to": "task_2"}],
            confidence=0.7,
        )
        result = validator.validate(decomp)
        assert result.is_valid is False
        assert any("task_999" in w for w in result.warnings)

    def test_single_task_dag(self, validator: DAGValidator) -> None:
        """Test DAG with single task."""
        decomp = _decomposition(
            tasks=[{"id": "task_1", "depends_on": []}],
            edges=[],
            confidence=0.95,
        )
        result = validator.validate(decomp)
        assert result.is_valid is True

    def test_empty_dag(self, validator: DAGValidator) -> None:
        """Test empty DAG — no crash, result has expected structure."""
        decomp = _decomposition(tasks=[], edges=[], confidence=0.8)
        result = validator.validate(decomp)
        assert hasattr(result, "is_valid")
        assert hasattr(result, "warnings")
