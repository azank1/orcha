"""Unit tests for deterministic DAG validation."""

from __future__ import annotations

import pytest
from planning_discovery.planning.validation.deterministic import DeterministicValidator

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Helpers — build minimal valid workflow dicts that satisfy the validator's
# required top-level fields: nodes, edges, entry_node_id, metadata.
# ---------------------------------------------------------------------------

_STANDARD_NODE_DEFAULTS = {
    "agent_id": "agent_001",
}


def _std_node(node_id: str, dependencies: list[str] | None = None, **extra) -> dict:
    return {
        "id": node_id,
        "type": "standard",
        "dependencies": dependencies or [],
        **_STANDARD_NODE_DEFAULTS,
        **extra,
    }


def _dag(
    nodes: list, edges: list, entry: str = "task_1", metadata: dict | None = None
) -> dict:
    return {
        "nodes": nodes,
        "edges": edges,
        "entry_node_id": entry,
        "metadata": metadata or {"confidence": 0.9},
    }


class TestDeterministicValidator:
    """Tests for deterministic validation logic."""

    @pytest.fixture
    def validator(self) -> DeterministicValidator:
        return DeterministicValidator()

    def test_validate_simple_dag(self, validator: DeterministicValidator) -> None:
        """Single-node DAG with all required fields passes."""
        workflow = _dag(
            nodes=[_std_node("task_1")],
            edges=[],
        )
        result = validator.validate(workflow)
        assert result.is_valid is True
        assert len(result.issues) == 0

    def test_validate_dag_with_dependencies(
        self, validator: DeterministicValidator
    ) -> None:
        """Two-node linear DAG with matching in-edges passes."""
        workflow = _dag(
            nodes=[
                _std_node("task_1"),
                _std_node("task_2", dependencies=["task_1"]),
            ],
            edges=[{"source": "task_1", "target": "task_2"}],
        )
        result = validator.validate(workflow)
        assert result.is_valid is True

    def test_missing_required_top_level_fields(
        self, validator: DeterministicValidator
    ) -> None:
        """DAG without entry_node_id and metadata is rejected immediately."""
        result = validator.validate({"nodes": [], "edges": []})
        assert result.is_valid is False
        assert any(
            "entry_node_id" in issue or "metadata" in issue for issue in result.issues
        )

    def test_duplicate_node_id(self, validator: DeterministicValidator) -> None:
        """Duplicate node IDs are flagged."""
        workflow = _dag(
            nodes=[_std_node("task_1"), _std_node("task_1")],
            edges=[],
        )
        result = validator.validate(workflow)
        assert result.is_valid is False
        assert any("duplicate" in issue.lower() for issue in result.issues)

    def test_edge_unknown_source(self, validator: DeterministicValidator) -> None:
        """Edge referencing an undeclared source node is flagged."""
        workflow = _dag(
            nodes=[_std_node("task_1")],
            edges=[{"source": "ghost_node", "target": "task_1"}],
        )
        result = validator.validate(workflow)
        assert result.is_valid is False
        assert any("ghost_node" in issue for issue in result.issues)

    def test_cycle_detection(self, validator: DeterministicValidator) -> None:
        """Cycle in the DAG is detected."""
        workflow = _dag(
            nodes=[
                _std_node("task_1", dependencies=["task_2"]),
                _std_node("task_2", dependencies=["task_1"]),
            ],
            edges=[
                {"source": "task_1", "target": "task_2"},
                {"source": "task_2", "target": "task_1"},
            ],
            entry="task_1",
        )
        result = validator.validate(workflow)
        assert result.is_valid is False
        assert any("cycle" in issue.lower() for issue in result.issues)

    def test_validate_router_node(self, validator: DeterministicValidator) -> None:
        """Router node with required fields (routing_key, branches) passes field check."""
        router = {
            "id": "router_1",
            "type": "router",
            "routing_key": "$task_1.output.value",
            "branches": [{"condition": "> 100", "target": "task_1"}],
            "dependencies": ["task_1"],
        }
        workflow = _dag(
            nodes=[_std_node("task_1"), router],
            edges=[{"source": "task_1", "target": "router_1"}],
        )
        result = validator.validate(workflow)
        # Router fields are present — no field-missing issues
        assert not any(
            "router_1" in issue and "missing" in issue for issue in result.issues
        )

    def test_empty_nodes_rejected(self, validator: DeterministicValidator) -> None:
        """Workflow with zero nodes is always invalid."""
        workflow = _dag(nodes=[], edges=[], entry="task_1")
        result = validator.validate(workflow)
        assert result.is_valid is False

    def test_result_has_issues_attribute(
        self, validator: DeterministicValidator
    ) -> None:
        """ValidationResult always exposes the .issues list."""
        result = validator.validate(_dag(nodes=[_std_node("task_1")], edges=[]))
        assert hasattr(result, "issues")
        assert isinstance(result.issues, list)
