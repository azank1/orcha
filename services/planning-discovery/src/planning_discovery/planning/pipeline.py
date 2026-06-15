"""Stage orchestrator for the 5-stage planning pipeline.

Pipeline:
  Stage 1  — Single-pass task decomposition      (SinglePassDecomposer)
  Stage 2a — Hybrid agent resolution             (HybridSearchPipeline + SemanticCoverageAnalyzer)
  Stage 2b — IO resolution                       (IOResolver)  [NEW]
  Stage 2c — Dependency refinement               (DependencyRefiner)  [NEW]
  Stage 3  — Tiered DAG validation               (TieredValidator)

Produces a ``WorkflowManifest`` ready for execution by the gateway.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import TYPE_CHECKING, Any

from ..schemas.workflow_manifest import NodeType, WorkflowManifest

if TYPE_CHECKING:
    from common.llm.src import LLMProvider

    from ..db.pool import AsyncpgPool
    from ..schemas.internal import CoverageResult, ValidationResult
from ..ranking import score_candidates
from ..utils.errors import (
    AmbiguousQueryError,
    NoAgentsFoundError,
    ValidationFailedError,
)
from .decomposition.single_pass_decomposer import SinglePassDecomposer
from .resolution.coverage_analyzer import SemanticCoverageAnalyzer
from .resolution.dependency_refiner import DependencyRefiner
from .resolution.hybrid_search import HybridSearchPipeline
from .resolution.io_resolver import IOResolver
from .validation.tiered_validator import TieredValidator

logger = logging.getLogger(__name__)


class OptimizedPlanningPipeline:
    """
    Top-level orchestrator that runs all five planning stages and returns a
    ``WorkflowManifest``.

    Instantiate once at application startup and reuse across requests.
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        pool: AsyncpgPool,
        *,
        decomposition_model: str,
        fallback_model: str,
        embedding_model: str,
        validation_model: str,
        top_k_candidates: int = 5,
        similarity_threshold: float = 0.75,
        confidence_threshold: float = 0.75,
    ) -> None:
        self._decomposer = SinglePassDecomposer(
            llm_provider=llm_provider,
            primary_model=decomposition_model,
            fallback_model=fallback_model,
            confidence_threshold=confidence_threshold,
        )
        self._search = HybridSearchPipeline(
            pool=pool,
            llm_provider=llm_provider,
            embedding_model=embedding_model,
            top_k=top_k_candidates,
        )
        self._coverage = SemanticCoverageAnalyzer(
            llm_provider=llm_provider,
            embedding_model=embedding_model,
            similarity_threshold=similarity_threshold,
        )
        # Stage 2b: IO resolution uses the lighter decomposition model for
        # extraction/matching — fast enough and cost-effective per task.
        # Inject search + coverage so the resolver can insert prerequisite tasks
        # (e.g. "search hotels" before "book hotel") when fields are unresolvable.
        self._io_resolver = IOResolver(
            llm_provider=llm_provider,
            model=decomposition_model,
            search_pipeline=self._search,
            coverage_analyzer=self._coverage,
        )
        # Stage 2c: pure graph logic, no LLM needed
        self._dependency_refiner = DependencyRefiner()
        self._validator = TieredValidator(
            llm_provider=llm_provider,
            validation_model=validation_model,
        )

    async def plan(
        self,
        user_query: str,
        context: dict[str, Any] | None = None,
    ) -> WorkflowManifest:
        """
        Run the full planning pipeline for *user_query*.

        Raises:
            AmbiguousQueryError:   If Stage 1 cannot decompose the query.
            NoAgentsFoundError:    If Stage 2a finds no suitable agents.
            ValidationFailedError: If Stage 3 rejects the generated DAG.
        """
        plan_id = str(uuid.uuid4())
        started_at = time.monotonic()
        logger.info("Planning started — plan_id=%s query='%.80s'", plan_id, user_query)

        # ── Stage 1: Decompose ────────────────────────────────────────────────
        decomp = await self._decomposer.decompose(user_query, context or {})
        if not decomp.tasks:
            raise AmbiguousQueryError(
                f"Could not decompose query into tasks: {user_query!r}"
            )

        logger.info("Stage 1 complete — %d task(s) extracted", len(decomp.tasks))
        logger.debug("Decomposition result: %s", decomp)

        # ── Stage 2a: Resolve agents (parallel across tasks) ─────────────────
        coverage_results = await asyncio.gather(
            *[self._resolve_task(task) for task in decomp.tasks],
            return_exceptions=True,
        )

        # Surface the first hard failure
        for result in coverage_results:
            if isinstance(result, Exception):
                raise result  # type: ignore[misc]

        coverage_map: dict[str, CoverageResult] = {
            task["id"]: cov
            for task, cov in zip(decomp.tasks, coverage_results, strict=True)
            if not isinstance(cov, Exception)
        }

        logger.info(
            "Stage 2a complete — coverage resolved for %d task(s)", len(coverage_map)
        )

        # Flatten coverage results into a task list enriched with agent info.
        # Chain expansion also happens here (sequential_chain → sub-tasks).
        resolved_tasks = self._flatten_coverage(decomp.tasks, coverage_map)

        # ── Stage 2b: IO Resolution ───────────────────────────────────────────
        # Sequential — each task sees the output schemas of previous tasks for
        # data dependency resolution.
        logger.info("Stage 2b: IO Resolution")
        io_resolved_tasks, hitl_node = await self._io_resolver.resolve_io(
            tasks=resolved_tasks,
            user_query=user_query,
        )
        logger.info(
            "Stage 2b complete — %d task(s) resolved, HITL=%s",
            len(io_resolved_tasks),
            hitl_node is not None,
        )

        # ── Stage 2c: Dependency Refinement ──────────────────────────────────
        logger.info("Stage 2c: Dependency Refinement")
        refined_dag = self._dependency_refiner.refine_dependencies(
            tasks=io_resolved_tasks,
            initial_edges=decomp.edges,
        )
        logger.info(
            "Stage 2c complete — %d edge(s) after transitive reduction",
            len(refined_dag["edges"]),
        )

        # ── Build final workflow dict ─────────────────────────────────────────
        all_nodes: list[dict[str, Any]] = []
        all_edges: list[dict[str, Any]] = list(refined_dag["edges"])

        # Prepend HITL node when present; it runs first and feeds missing inputs
        # to all tasks that need them.
        if hitl_node:
            all_nodes.append(hitl_node)
            # Add edges from HITL → every task with unresolved inputs
            for task in io_resolved_tasks:
                if task.get("unresolved_inputs"):
                    all_edges.insert(
                        0,
                        {
                            "from": hitl_node["id"],
                            "to": task["id"],
                            "condition": None,
                        },
                    )

        # Translate edges to source/target format expected by the validator
        translated_edges = self._translate_edges(all_edges)

        # Derive per-node in-edges from the final translated edge list so that each
        # node's ``dependencies`` field exactly matches the actual edges going into it.
        # This must happen AFTER both refinement and HITL edge insertion.
        node_actual_deps: dict[str, list[str]] = {}
        for edge in translated_edges:
            tgt = edge["target"]
            src = edge["source"]
            deps = node_actual_deps.setdefault(tgt, [])
            if src not in deps:
                deps.append(src)

        for task in io_resolved_tasks:
            node = self._make_standard_node(task)
            node["dependencies"] = node_actual_deps.get(task["id"], [])
            all_nodes.append(node)

        # Determine entry node
        entry_node_id: str = (
            hitl_node["id"] if hitl_node else (all_nodes[0]["id"] if all_nodes else "")
        )

        workflow_dict: dict[str, Any] = {
            "id": plan_id,
            "nodes": all_nodes,
            "edges": translated_edges,
            "entry_node_id": entry_node_id,
            "metadata": {
                "original_query": user_query,
                "node_count": len(all_nodes),
                "edge_count": len(translated_edges),
            },
        }

        # ── Stage 3: Validate ─────────────────────────────────────────────────
        validation: ValidationResult = await self._validator.validate(
            workflow_dict, original_query=user_query
        )
        if not validation.is_valid:
            raise ValidationFailedError(
                f"Workflow validation failed ({validation.tier}): {validation.issues}"
            )

        elapsed_ms = (time.monotonic() - started_at) * 1000
        logger.info(
            "Planning complete — plan_id=%s elapsed=%.0fms nodes=%d",
            plan_id,
            elapsed_ms,
            len(workflow_dict.get("nodes", [])),
        )

        return WorkflowManifest(**workflow_dict)

    # ------------------------------------------------------------------
    # Stage 2a helpers
    # ------------------------------------------------------------------

    async def _resolve_task(self, task: dict[str, Any]) -> CoverageResult:
        """Search for agents, apply routing scores, then compute coverage."""
        task_description = task.get("description", task.get("id", ""))
        top_candidates = await self._search.search(task_description)
        if not top_candidates:
            raise NoAgentsFoundError(f"No agents found for task: {task_description!r}")

        # Apply routing scores — gates unreliable agents and sorts by composite score.
        # Falls back to unscored list on any import failure (common_pricing not installed).
        try:
            registry_stats = await self._fetch_registry_stats(task.get("task_category"))
            med_latency = (
                registry_stats.get("median_latency_ms") if registry_stats else None
            )
            med_fee_raw = (
                registry_stats.get("median_base_fee_usd") if registry_stats else None
            )
            from decimal import Decimal

            med_fee = Decimal(str(med_fee_raw)) if med_fee_raw is not None else None
            top_candidates = score_candidates(top_candidates, med_latency, med_fee)
            logger.debug(
                "_resolve_task: scored %d candidates for task=%s",
                len(top_candidates),
                task.get("id"),
            )
        except Exception:
            logger.debug(
                "_resolve_task: routing score skipped (non-fatal)", exc_info=True
            )

        if not top_candidates:
            raise NoAgentsFoundError(
                f"No agents passed routing score gates for task: {task_description!r}"
            )

        return await self._coverage.analyze_coverage(task, top_candidates)

    async def _fetch_registry_stats(self, task_category: str | None) -> dict | None:
        """Fetch RegistryStats medians for the given task_category (best-effort)."""
        if not task_category:
            return None
        try:
            import os

            from common.database.src.generated_client import Prisma

            # Prefer the DSN exposed by AsyncpgPool; fall back to DATABASE_URL env var.
            dsn = getattr(self._search._pool, "_dsn", None) or os.environ.get(
                "DATABASE_URL", ""
            )
            db = Prisma(datasource={"url": dsn})
            await db.connect()
            try:
                stats = await db.registrystats.find_unique(
                    where={"task_category": task_category}
                )
                if stats:
                    return {
                        "median_latency_ms": stats.median_latency_ms,
                        "median_base_fee_usd": str(stats.median_base_fee_usd)
                        if stats.median_base_fee_usd
                        else None,
                    }
            finally:
                await db.disconnect()
        except Exception:
            logger.debug("_fetch_registry_stats: failed for category=%s", task_category)
        return None

    def _flatten_coverage(
        self,
        decomp_tasks: list[dict[str, Any]],
        coverage_map: dict[str, CoverageResult],
    ) -> list[dict[str, Any]]:
        """
        Convert coverage results into a flat list of tasks enriched with agent info.

        Handles sequential chain expansion (task_id → task_id__step_0, __step_1, …).
        Each returned task dict has ``agent_id`` and ``agent_manifest`` set so that
        Stage 2b (IOResolver) can access the capability schemas.
        """
        resolved: list[dict[str, Any]] = []

        for task in decomp_tasks:
            task_id = task["id"]
            coverage = coverage_map.get(task_id)
            if coverage is None:
                resolved.append(dict(task))
                continue

            if coverage.strategy == "single_agent" and coverage.agent:
                task_copy = dict(task)
                task_copy["agent_id"] = coverage.agent.agent_id
                task_copy["agent_manifest"] = coverage.agent.manifest
                task_copy["coverage_strategy"] = "single_agent"
                resolved.append(task_copy)

            elif coverage.strategy == "sequential_chain" and coverage.chain:
                # Expand chain into sub-tasks chained sequentially
                prev_step_id: str | None = None
                for i, agent in enumerate(coverage.chain):
                    step_id = f"{task_id}__step_{i}"
                    task_copy = dict(task)
                    task_copy["id"] = step_id
                    task_copy["agent_id"] = agent.agent_id
                    task_copy["agent_manifest"] = agent.manifest
                    task_copy["coverage_strategy"] = "sequential_chain"
                    # Each step depends on the previous step
                    if prev_step_id:
                        existing_deps = list(task_copy.get("depends_on", []))
                        if prev_step_id not in existing_deps:
                            existing_deps.append(prev_step_id)
                        task_copy["depends_on"] = existing_deps
                    resolved.append(task_copy)
                    prev_step_id = step_id

            else:
                # recursive_subgraph — placeholder with first available agent
                task_copy = dict(task)
                if coverage.available_agents:
                    task_copy["agent_id"] = coverage.available_agents[0].agent_id
                    task_copy["agent_manifest"] = coverage.available_agents[0].manifest
                task_copy["orchestration_hint"] = "recursive_subgraph"
                resolved.append(task_copy)

        return resolved

    # ------------------------------------------------------------------
    # Node / edge assembly helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_standard_node(task: dict[str, Any]) -> dict[str, Any]:
        """
        Build a standard node dict from an IO-resolved task.

        For tasks that went through Stage 2b the ``capability`` and ``task``
        blocks carry the real schemas and resolved inputs.  For pass-through
        tasks (router / system_tool / unresolved) we fall back to the
        decomposition-level fields.
        """
        node_type = task.get("type", NodeType.STANDARD)
        # Coerce router nodes that lack required routing fields to standard — the
        # decomposer sometimes labels a planning task as "router" without providing
        # routing_key and branches, which would fail deterministic validation.
        if node_type == "router" and not (
            task.get("routing_key") and task.get("branches")
        ):
            node_type = NodeType.STANDARD

        node: dict[str, Any] = {
            "id": task["id"],
            "type": node_type,
            "agent_id": task.get("agent_id", ""),
            "description": task.get("description", ""),
            "dependencies": task.get("depends_on", []),
            "config": {},
        }

        # IO-resolved capability block (may be absent for non-agent tasks)
        if task.get("capability"):
            node["capability"] = task["capability"]

        # Task descriptor with resolved inputs
        if task.get("task"):
            node["task"] = task["task"]

        if task.get("unresolved_inputs"):
            node["unresolved_inputs"] = task["unresolved_inputs"]

        if task.get("field_mappings"):
            node["field_mappings"] = task["field_mappings"]

        if task.get("orchestration_hint"):
            node["orchestration_hint"] = task["orchestration_hint"]

        # HITL system_tool pass-through fields
        if task.get("type") == NodeType.SYSTEM_TOOL:
            node["tool_name"] = task.get("tool_name") or task.get("tool", "")
            node["inputs"] = task.get("inputs", {})
            node["outputs"] = task.get("outputs", {})

        return node

    @staticmethod
    def _translate_edges(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Normalise all edges to ``source``/``target`` format required by the validator.

        DependencyRefiner returns edges with ``from``/``to``; the validator
        and workflow manifest expect ``source``/``target``.
        """
        translated: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for e in edges:
            src = e.get("source") or e.get("from", "")
            tgt = e.get("target") or e.get("to", "")
            if not src or not tgt:
                continue
            key = (src, tgt)
            if key in seen:
                continue
            seen.add(key)
            edge: dict[str, Any] = {"source": src, "target": tgt}
            if e.get("condition") is not None:
                edge["condition"] = e["condition"]
            translated.append(edge)
        return translated

    @staticmethod
    def _reroute_edges(
        edges: list[dict[str, Any]],
        old_id: str,
        new_head_id: str,
        new_tail_id: str,
    ) -> None:
        """Rewrite edges that reference *old_id* to use chain head/tail."""
        for edge in edges:
            if edge.get("target") == old_id:
                edge["target"] = new_head_id
            if edge.get("source") == old_id:
                edge["source"] = new_tail_id
