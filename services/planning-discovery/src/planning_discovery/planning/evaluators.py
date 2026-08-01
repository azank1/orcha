"""Domain-specific evaluators for the P&D planning pipeline.

These evaluators assess the structural quality of LLM outputs at each
stage and are used for post-call validation (and future loopllm integration).

Each evaluator's ``evaluate()`` returns an ``EvaluationResult`` with:
  - ``score``        — float 0.0–1.0
  - ``passed``       — bool (True if quality threshold met)
  - ``deficiencies`` — list of specific issues found
  - ``sub_scores``   — per-dimension breakdown
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

# ── Shared result type ────────────────────────────────────────────────────────


@dataclass
class EvaluationResult:
    """Result from a single evaluator pass."""

    score: float
    passed: bool = False
    deficiencies: list[str] = field(default_factory=list)
    sub_scores: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


# ── Stage 1 evaluator ─────────────────────────────────────────────────────────


class DecompositionEvaluator:
    """Evaluates structural quality of a task decomposition output.

    Checks:
    - Valid JSON with a ``tasks`` array
    - Each task has required fields: id, type, description, depends_on
    - No duplicate task IDs
    - No circular dependencies (DFS cycle detection)
    - All task types are valid (agent_task | router | system_tool)
    - Descriptions are meaningful (>= 10 chars)
    """

    VALID_TASK_TYPES = {"agent_task", "router", "system_tool"}

    def evaluate(self, output: str, context: dict[str, Any]) -> EvaluationResult:
        deficiencies: list[str] = []
        sub_scores: dict[str, float] = {}

        # ── Parse JSON ────────────────────────────────────────────────
        try:
            data = json.loads(output)
        except Exception:
            return EvaluationResult(
                score=0.0,
                passed=False,
                deficiencies=["Output is not valid JSON"],
                sub_scores={"json_valid": 0.0},
            )
        sub_scores["json_valid"] = 1.0

        tasks = data.get("tasks", [])
        if not tasks:
            return EvaluationResult(
                score=0.1,
                passed=False,
                deficiencies=["No tasks found in decomposition"],
                sub_scores={"json_valid": 1.0, "has_tasks": 0.0},
            )
        sub_scores["has_tasks"] = 1.0

        # ── Required fields ───────────────────────────────────────────
        required = {"id", "type", "description", "depends_on"}
        missing_fields = 0
        for t in tasks:
            missing = required - set(t.keys())
            if missing:
                missing_fields += 1
                deficiencies.append(
                    f"Task '{t.get('id', '?')}' missing fields: {missing}"
                )
        sub_scores["required_fields"] = 1.0 - (missing_fields / len(tasks))

        # ── Valid task types ──────────────────────────────────────────
        invalid_types = 0
        for t in tasks:
            if t.get("type") not in self.VALID_TASK_TYPES:
                invalid_types += 1
                deficiencies.append(
                    f"Task '{t.get('id', '?')}' has invalid type '{t.get('type')}'. "
                    f"Valid types: {self.VALID_TASK_TYPES}"
                )
        sub_scores["valid_types"] = 1.0 - (invalid_types / len(tasks))

        # ── No duplicate IDs ──────────────────────────────────────────
        ids = [t.get("id") for t in tasks]
        unique_ids = set(ids)
        if len(unique_ids) < len(ids):
            dup_count = len(ids) - len(unique_ids)
            deficiencies.append(f"{dup_count} duplicate task ID(s) found")
            sub_scores["unique_ids"] = 1.0 - (dup_count / len(ids))
        else:
            sub_scores["unique_ids"] = 1.0

        # ── No circular dependencies ──────────────────────────────────
        id_set = {t.get("id") for t in tasks}
        has_cycle = self._detect_cycles(tasks, id_set)
        if has_cycle:
            deficiencies.append("Circular dependency detected in task graph")
            sub_scores["no_cycles"] = 0.0
        else:
            sub_scores["no_cycles"] = 1.0

        # ── Description quality ───────────────────────────────────────
        short_descs = 0
        for t in tasks:
            desc = t.get("description", "")
            if len(desc) < 10:
                short_descs += 1
                deficiencies.append(
                    f"Task '{t.get('id', '?')}' has a too-short description: '{desc}'"
                )
        sub_scores["description_quality"] = 1.0 - (short_descs / len(tasks))

        # ── Aggregate ─────────────────────────────────────────────────
        weights = {
            "json_valid": 0.15,
            "has_tasks": 0.10,
            "required_fields": 0.20,
            "valid_types": 0.15,
            "unique_ids": 0.15,
            "no_cycles": 0.15,
            "description_quality": 0.10,
        }
        total = sum(sub_scores.get(k, 0) * w for k, w in weights.items())
        passed = total >= 0.7 and not has_cycle

        return EvaluationResult(
            score=total,
            passed=passed,
            deficiencies=deficiencies,
            sub_scores=sub_scores,
        )

    @staticmethod
    def _detect_cycles(tasks: list[dict[str, Any]], id_set: set) -> bool:
        """Detect cycles in the dependency graph via DFS."""
        graph: dict[str, list[str]] = {}
        for t in tasks:
            tid = t.get("id", "")
            deps = t.get("depends_on", [])
            graph[tid] = [d for d in deps if d in id_set]

        visited: set = set()
        rec_stack: set = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.discard(node)
            return False

        return any(node not in visited and dfs(node) for node in graph)


# ── Stage 2 evaluator ─────────────────────────────────────────────────────────


class ResolutionEvaluator:
    """Evaluates agent resolution quality.

    Checks:
    - All tasks have agent assignments
    - All tasks have capability assignments
    - Assigned agent IDs exist in the registry (when context provides them)
    """

    def evaluate(self, output: str, context: dict[str, Any]) -> EvaluationResult:
        deficiencies: list[str] = []
        sub_scores: dict[str, float] = {}

        try:
            data = json.loads(output)
        except Exception:
            return EvaluationResult(
                score=0.0,
                passed=False,
                deficiencies=["Output is not valid JSON"],
            )
        sub_scores["json_valid"] = 1.0

        nodes = data.get("nodes", data.get("resolved_tasks", []))
        if not nodes:
            return EvaluationResult(
                score=0.1,
                passed=False,
                deficiencies=["No resolved nodes found"],
                sub_scores={"json_valid": 1.0, "has_nodes": 0.0},
            )
        sub_scores["has_nodes"] = 1.0

        unresolved = 0
        for node in nodes:
            if not node.get("agent_id"):
                unresolved += 1
                deficiencies.append(f"Node '{node.get('id', '?')}' has no agent_id")
        sub_scores["agent_assigned"] = 1.0 - (unresolved / len(nodes))

        no_cap = 0
        for node in nodes:
            cap = node.get("capability", {})
            if not cap.get("capability_id"):
                no_cap += 1
                deficiencies.append(
                    f"Node '{node.get('id', '?')}' has no capability_id"
                )
        sub_scores["capability_assigned"] = 1.0 - (no_cap / len(nodes))

        known_agents = context.get("known_agent_ids", set())
        if known_agents:
            unknown = 0
            for node in nodes:
                aid = node.get("agent_id", "")
                if aid and aid not in known_agents:
                    unknown += 1
                    deficiencies.append(f"Agent '{aid}' not found in registry")
            sub_scores["agents_valid"] = 1.0 - (unknown / len(nodes))
        else:
            sub_scores["agents_valid"] = 1.0

        weights = {
            "json_valid": 0.15,
            "has_nodes": 0.15,
            "agent_assigned": 0.30,
            "capability_assigned": 0.25,
            "agents_valid": 0.15,
        }
        total = sum(sub_scores.get(k, 0) * w for k, w in weights.items())
        passed = total >= 0.7 and unresolved == 0

        return EvaluationResult(
            score=total,
            passed=passed,
            deficiencies=deficiencies,
            sub_scores=sub_scores,
        )


# ── Stage 3 evaluator ─────────────────────────────────────────────────────────


class PlanAssemblyEvaluator:
    """Evaluates assembled workflow plan quality.

    Checks:
    - Valid JSON with nodes and edges arrays
    - All edge source/target references point to existing nodes
    - At least one terminal node (a node with no outgoing edges)
    - At least one root node (a node with no incoming edges)
    - All nodes have agent assignments
    """

    def evaluate(self, output: str, context: dict[str, Any]) -> EvaluationResult:
        deficiencies: list[str] = []
        sub_scores: dict[str, float] = {}

        try:
            data = json.loads(output)
        except Exception:
            return EvaluationResult(
                score=0.0,
                passed=False,
                deficiencies=["Output is not valid JSON"],
            )
        sub_scores["json_valid"] = 1.0

        nodes = data.get("nodes", [])
        edges = data.get("edges", [])

        if not nodes:
            return EvaluationResult(
                score=0.1,
                passed=False,
                deficiencies=["No nodes in assembled plan"],
                sub_scores={"json_valid": 1.0, "has_nodes": 0.0},
            )
        sub_scores["has_nodes"] = 1.0

        node_ids = {n.get("id") for n in nodes}

        invalid_edges = 0
        for edge in edges:
            src = edge.get("source") or edge.get("from")
            tgt = edge.get("target") or edge.get("to")
            if src not in node_ids:
                invalid_edges += 1
                deficiencies.append(f"Edge source '{src}' not found in nodes")
            if tgt not in node_ids:
                invalid_edges += 1
                deficiencies.append(f"Edge target '{tgt}' not found in nodes")
        sub_scores["edge_validity"] = max(
            1.0 - (invalid_edges / max(len(edges) * 2, 1)), 0.0
        )

        sources = {(e.get("source") or e.get("from")) for e in edges}
        if not (node_ids - sources):
            deficiencies.append("No terminal node found (possible cycle)")
            sub_scores["has_terminal"] = 0.0
        else:
            sub_scores["has_terminal"] = 1.0

        targets = {(e.get("target") or e.get("to")) for e in edges}
        roots = node_ids - targets
        if not roots and len(nodes) > 1:
            deficiencies.append("No root node found")
            sub_scores["has_root"] = 0.0
        else:
            sub_scores["has_root"] = 1.0

        no_agent = sum(1 for n in nodes if not n.get("agent_id"))
        sub_scores["agents_assigned"] = 1.0 - (no_agent / len(nodes))
        if no_agent:
            deficiencies.append(f"{no_agent} node(s) without agent assignment")

        weights = {
            "json_valid": 0.10,
            "has_nodes": 0.15,
            "edge_validity": 0.25,
            "has_terminal": 0.15,
            "has_root": 0.15,
            "agents_assigned": 0.20,
        }
        total = sum(sub_scores.get(k, 0) * w for k, w in weights.items())
        passed = total >= 0.7 and invalid_edges == 0

        return EvaluationResult(
            score=total,
            passed=passed,
            deficiencies=deficiencies,
            sub_scores=sub_scores,
        )


# ── Composite evaluator ───────────────────────────────────────────────────────


class CompositeEvaluator:
    """Combines multiple evaluators with weighted scoring.

    Example::

        evaluator = CompositeEvaluator([
            ("decomp", DecompositionEvaluator(), 0.6),
            ("resolution", ResolutionEvaluator(), 0.4),
        ])
    """

    def __init__(self, evaluators: list[tuple[str, Any, float]]):
        """
        Args:
            evaluators: List of (name, evaluator, weight) tuples.
                Weights should sum to 1.0.
        """
        self.evaluators = evaluators

    def evaluate(self, output: str, context: dict[str, Any]) -> EvaluationResult:
        all_deficiencies: list[str] = []
        all_sub_scores: dict[str, float] = {}
        weighted_score = 0.0

        for name, evaluator, weight in self.evaluators:
            result = evaluator.evaluate(output, context)
            weighted_score += result.score * weight
            for d in result.deficiencies:
                all_deficiencies.append(f"[{name}] {d}")
            for k, v in result.sub_scores.items():
                all_sub_scores[f"{name}.{k}"] = v

        passed = weighted_score >= 0.7 and all(
            e.evaluate(output, context).passed for _, e, _ in self.evaluators
        )

        return EvaluationResult(
            score=weighted_score,
            passed=passed,
            deficiencies=all_deficiencies,
            sub_scores=all_sub_scores,
        )
