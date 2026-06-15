"""Stage 2b — IO Resolution.

Resolves exact agent capabilities and input/output schemas for each task.
Extracts input values from the user query and identifies data dependencies
between tasks.  Creates a human-in-the-loop (HITL) node when required inputs
cannot be satisfied from the query or previous task outputs.

Prerequisite detection: when a required input cannot be sourced from the user
query or existing previous-task outputs, the resolver attempts to detect
whether a missing upstream task (e.g. "search hotels" before "book hotel")
would naturally produce that field.  If found, the resolver inserts a new
resolved task for that prerequisite into the workflow on the fly.
"""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from .prompts import (
    CAPABILITY_SELECTION_PROMPT,
    FIELD_MATCHING_PROMPT,
    INPUT_EXTRACTION_PROMPT,
    PREREQUISITE_DETECTION_PROMPT,
)

if TYPE_CHECKING:
    from common.llm.src import LLMProvider

    from .coverage_analyzer import SemanticCoverageAnalyzer
    from .hybrid_search import HybridSearchPipeline

logger = logging.getLogger(__name__)

# Minimum confidence to accept a semantic field match from a previous task.
# Raised from 0.7 → 0.85 to prevent hallucinated cross-domain matches.
_FIELD_MATCH_CONFIDENCE = 0.85


class PrerequisiteInfo(BaseModel):
    """Describes a missing upstream task detected during input resolution."""

    field_name: str
    action_description: str  # e.g. "search hotels in the destination city"
    capability_hint: str  # e.g. "hotel search"


class IOResolutionResult(BaseModel):
    """Result of IO resolution for a single task."""

    capability_id: str
    capability_type: str  # TOOL, RESOURCE, PROMPT
    capability_name: str
    input_schema: dict[str, Any] = Field(default_factory=dict)
    filled_inputs: dict[str, Any] = Field(default_factory=dict)
    missing_required_inputs: list[str] = Field(default_factory=list)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    # Task IDs whose outputs feed into this task's inputs
    data_dependencies: list[str] = Field(default_factory=list)
    # Semantic field mappings: source_task → source_field → target_field
    field_mappings: list[dict[str, Any]] = Field(default_factory=list)
    # Prerequisites detected but not yet inserted (handled by resolve_io loop)
    detected_prerequisites: list[PrerequisiteInfo] = Field(default_factory=list)


class IOResolver:
    """
    Resolves exact capabilities and input/output schemas for each task.

    Process per task:
    1. Select best capability from the agent's manifest
    2. Extract input values from the user query (LLM)
    3. Resolve remaining inputs from previous task outputs (semantic match, ≥0.85)
    4. Detect missing prerequisite tasks and insert them on the fly (if
       search_pipeline + coverage_analyzer are provided)
    5. Use schema defaults for optional fields
    6. Identify missing required inputs → HITL node
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        model: str | None = None,
        search_pipeline: HybridSearchPipeline | None = None,
        coverage_analyzer: SemanticCoverageAnalyzer | None = None,
    ) -> None:
        self._llm = llm_provider
        self._model = model
        self._search_pipeline = search_pipeline
        self._coverage_analyzer = coverage_analyzer

    # ------------------------------------------------------------------
    # Static helpers — type safety and deduplication
    # ------------------------------------------------------------------

    @staticmethod
    def _types_strictly_compatible(
        input_schema: dict[str, Any],
        output_schema: dict[str, Any],
    ) -> bool:
        """
        Return True only when the two JSON-Schema types are assignment-compatible.

        Rules:
        - number  ↔ integer  → compatible (both numeric)
        - string  (format: date/date-time) ↔ string (format: date/date-time) → compatible
        - string  (no date format) ↔ string (date format) → NOT compatible
        - array   ↔ non-array  → NOT compatible
        - object  ↔ non-object → NOT compatible
        - any other base-type mismatch → NOT compatible
        """
        in_type = input_schema.get("type", "")
        out_type = output_schema.get("type", "")

        # Numeric flexibility: number and integer are mutually assignable
        if {in_type, out_type} == {"number", "integer"}:
            return True

        if in_type != out_type:
            return False

        # Both are strings — check date format consistency
        if in_type == "string":
            in_fmt = input_schema.get("format", "")
            out_fmt = output_schema.get("format", "")
            date_formats = {"date", "date-time"}
            if in_fmt in date_formats or out_fmt in date_formats:
                # One side is a date — both must be date-like to be compatible
                return in_fmt in date_formats and out_fmt in date_formats

        return True

    @staticmethod
    def _deduplicate_previous_tasks(
        tasks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Remove tasks with duplicate (agent_id, output_schema) pairs.

        Prevents the LLM from seeing the same output fields twice when a
        prerequisite task with the same agent was already inserted, which
        could cause it to propose the same match redundantly.
        """
        seen: set[str] = set()
        result: list[dict[str, Any]] = []
        for task in tasks:
            agent_id = task.get("agent_id", "")
            schema = task.get("capability", {}).get("output_schema", {})
            key = f"{agent_id}:{json.dumps(schema, sort_keys=True)}"
            if key not in seen:
                seen.add(key)
                result.append(task)
        return result

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def resolve_io(
        self,
        tasks: list[dict[str, Any]],
        user_query: str,
        model: str | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
        """
        Resolve IO for all tasks sequentially.

        Sequential processing is required so that each task can reference the
        output schemas of previously resolved tasks when looking for data
        dependencies.  Prerequisite tasks are inserted inline when detected,
        immediately becoming available to subsequent field resolution.

        Returns:
            (resolved_tasks, hitl_node)
            hitl_node is None when all required inputs are satisfied.
        """
        effective_model = model or self._model
        resolved_tasks: list[dict[str, Any]] = []
        # task_id → list of missing field names that need human input
        all_missing_inputs: dict[str, list[str]] = {}

        for task in tasks:
            agent_manifest = task.get("agent_manifest", {})
            if not agent_manifest or task.get("type") != "agent_task":
                # Pass-through router / system_tool nodes unchanged
                resolved_tasks.append(task)
                continue

            try:
                capability = await self._select_capability(
                    task=task,
                    agent_manifest=agent_manifest,
                    model=effective_model,
                )
            except (ValueError, IndexError) as exc:
                logger.warning(
                    "Capability selection failed for task %s: %s — skipping IO resolution",
                    task.get("id"),
                    exc,
                )
                resolved_tasks.append(task)
                continue

            io_result = await self._resolve_inputs(
                task=task,
                capability=capability,
                user_query=user_query,
                previous_tasks=resolved_tasks,
                model=effective_model,
            )

            # ── Prerequisite insertion ────────────────────────────────────
            # For each field where we detected a missing prerequisite task,
            # attempt to search for an agent, resolve it, and insert it into
            # the workflow so the field can be wired via a $tasks.* reference.
            still_unhandled: list[PrerequisiteInfo] = []
            for prereq in list(io_result.detected_prerequisites):
                prereq_task = await self._create_prerequisite_task(
                    prereq=prereq,
                    parent_task=task,
                    previous_tasks=resolved_tasks,
                    user_query=user_query,
                    model=effective_model,
                )
                if prereq_task is None:
                    # No agent found — field stays as HITL
                    still_unhandled.append(prereq)
                    continue

                resolved_tasks.append(prereq_task)
                logger.info(
                    "Inserted prerequisite task '%s' for field '%s' (parent: %s)",
                    prereq_task["id"],
                    prereq.field_name,
                    task.get("id"),
                )

                # Re-run semantic matching now that the prereq is visible
                field_schema = (
                    capability.get("input_schema", {})
                    .get("properties", {})
                    .get(prereq.field_name, {})
                )
                match = await self._find_providing_task(
                    field_name=prereq.field_name,
                    field_schema=field_schema,
                    previous_tasks=resolved_tasks,
                    model=effective_model,
                )
                if match:
                    providing_task = match["task"]
                    output_field = match["output_field"]
                    io_result.filled_inputs[prereq.field_name] = (
                        f"$tasks.{providing_task['id']}.output.{output_field}"
                    )
                    dep_id = providing_task["id"]
                    if dep_id not in io_result.data_dependencies:
                        io_result.data_dependencies.append(dep_id)
                    io_result.field_mappings.append(
                        {
                            "source_task": dep_id,
                            "source_field": output_field,
                            "target_field": prereq.field_name,
                            "confidence": match["confidence"],
                            "reasoning": match.get(
                                "reasoning", "prerequisite-inserted"
                            ),
                        }
                    )
                    if prereq.field_name in io_result.missing_required_inputs:
                        io_result.missing_required_inputs.remove(prereq.field_name)
                else:
                    # Prereq was inserted but semantic match still failed —
                    # fall back to HITL for this field.
                    still_unhandled.append(prereq)

            io_result.detected_prerequisites = still_unhandled

            if io_result.missing_required_inputs:
                all_missing_inputs[task["id"]] = io_result.missing_required_inputs
                logger.info(
                    "Task %s has %d missing required inputs: %s",
                    task["id"],
                    len(io_result.missing_required_inputs),
                    io_result.missing_required_inputs,
                )

            resolved_task = self._create_resolved_task(task, io_result)
            resolved_tasks.append(resolved_task)

        hitl_node: dict[str, Any] | None = None
        if all_missing_inputs:
            hitl_node = self._create_hitl_node(all_missing_inputs)
            logger.info(
                "Created HITL node for %d task(s) with missing inputs",
                len(all_missing_inputs),
            )

        return resolved_tasks, hitl_node

    # ------------------------------------------------------------------
    # Capability selection
    # ------------------------------------------------------------------

    async def _select_capability(
        self,
        task: dict[str, Any],
        agent_manifest: dict[str, Any],
        model: str | None = None,
    ) -> dict[str, Any]:
        """
        Select the best capability from the agent manifest for this task.

        Strategy:
        1. Flatten all capabilities (tools / resources / prompts) into a list
        2. Use LLM to pick the index of the best match
        3. Return the capability dict with normalised keys
        """
        capabilities = agent_manifest.get("capabilities", [])

        # Manifest may arrive in nested emerge.yaml format or flat Kafka format.
        # The flat format (from _fetch_agents()) is a list of dicts with 'type' key.
        if isinstance(capabilities, list):
            all_caps = capabilities
        elif isinstance(capabilities, dict):
            # emerge.yaml nested format: {"tools": [...], "resources": [...]}
            all_caps = []
            for cap_type in ("tools", "resources", "prompts"):
                for cap in capabilities.get(cap_type, []):
                    all_caps.append(
                        {
                            "type": cap_type.rstrip(
                                "s"
                            ).upper(),  # TOOL / RESOURCE / PROMPT
                            "capability_id": cap.get("name"),
                            "name": cap.get("name"),
                            "description": cap.get("description", ""),
                            "input_schema": cap.get("inputSchema")
                            or cap.get("input_schema", {}),
                            "output_schema": cap.get("outputSchema")
                            or cap.get("output_schema", {}),
                        }
                    )
        else:
            all_caps = []

        if not all_caps:
            raise ValueError(f"Agent {agent_manifest.get('id')} has no capabilities")

        # Normalise list items to ensure required keys exist
        normalised: list[dict[str, Any]] = []
        for cap in all_caps:
            normalised.append(
                {
                    "capability_id": cap.get("capability_id") or cap.get("name", ""),
                    "type": (cap.get("type") or "TOOL").upper().rstrip("S"),
                    "name": cap.get("name", ""),
                    "description": cap.get("description", ""),
                    "input_schema": cap.get("input_schema") or {},
                    "output_schema": cap.get("output_schema") or {},
                }
            )

        if len(normalised) == 1:
            return normalised[0]

        task_description = task.get("description", "")
        prompt = CAPABILITY_SELECTION_PROMPT.format(
            task_description=task_description,
            capabilities_json=json.dumps(
                [
                    {"index": i, "name": c["name"], "description": c["description"]}
                    for i, c in enumerate(normalised)
                ],
                indent=2,
            ),
        )

        response = await self._llm.complete(
            model=model or "",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        raw = response.strip()
        try:
            selected_idx = int(raw)
        except ValueError:
            m = re.search(r"\b(\d+)\b", raw)
            if m:
                selected_idx = int(m.group(1))
                logger.debug(
                    "Extracted capability index %d from verbose LLM response",
                    selected_idx,
                )
            else:
                logger.warning(
                    "LLM returned non-integer capability index %r — defaulting to 0",
                    raw,
                )
                selected_idx = 0

        return normalised[max(0, min(selected_idx, len(normalised) - 1))]

    # ------------------------------------------------------------------
    # Input resolution
    # ------------------------------------------------------------------

    async def _resolve_inputs(
        self,
        task: dict[str, Any],
        capability: dict[str, Any],
        user_query: str,
        previous_tasks: list[dict[str, Any]],
        model: str | None = None,
    ) -> IOResolutionResult:
        """
        Resolve all required inputs for this task using a 5-strategy waterfall.

        Per field:
          1. Extract from user query (LLM)
          2. Semantic match from previous task output (≥0.85 confidence, LLM)
          3. Detect missing prerequisite task (LLM, only if search pipeline available)
          4. Use schema default value
          5. Mark as missing required (→ HITL)
        """
        input_schema = capability.get("input_schema") or {}
        properties: dict[str, Any] = input_schema.get("properties", {})
        required_fields: list[str] = input_schema.get("required", [])

        # Step 1: batch-extract all field values from the query in a single LLM call
        extracted_from_query = await self._extract_from_query(
            user_query=user_query,
            input_schema=input_schema,
            task_description=task.get("description", ""),
            model=model,
        )

        filled_inputs: dict[str, Any] = {}
        missing_required: list[str] = []
        data_dependencies: list[str] = []
        field_mappings: list[dict[str, Any]] = []
        detected_prerequisites: list[PrerequisiteInfo] = []

        for field_name, field_schema in properties.items():
            # Strategy 1: from query extraction
            extracted_value = extracted_from_query.get(field_name)
            if extracted_value is not None:
                filled_inputs[field_name] = extracted_value
                continue

            # Strategy 2: semantic match to a previous task output (threshold 0.85)
            providing_info = await self._find_providing_task(
                field_name=field_name,
                field_schema=field_schema,
                previous_tasks=previous_tasks,
                model=model,
            )
            if providing_info:
                providing_task = providing_info["task"]
                output_field = providing_info["output_field"]
                # Build a $tasks data reference for runtime resolution
                filled_inputs[field_name] = (
                    f"$tasks.{providing_task['id']}.output.{output_field}"
                )
                dep_id = providing_task["id"]
                if dep_id not in data_dependencies:
                    data_dependencies.append(dep_id)
                field_mappings.append(
                    {
                        "source_task": dep_id,
                        "source_field": output_field,
                        "target_field": field_name,
                        "confidence": providing_info["confidence"],
                        "reasoning": providing_info.get("reasoning", ""),
                    }
                )
                continue

            # Strategy 3: detect missing prerequisite task
            # Only run when the search pipeline is available and the field is required.
            if (
                self._search_pipeline
                and self._coverage_analyzer
                and field_name in required_fields
            ):
                prereq = await self._detect_missing_prerequisite(
                    field_name=field_name,
                    field_schema=field_schema,
                    task_description=task.get("description", ""),
                    previous_tasks=previous_tasks,
                    model=model,
                )
                if prereq:
                    detected_prerequisites.append(prereq)
                    # The actual insertion happens in resolve_io() after this method
                    # returns, so we skip to the next field for now.
                    continue

            # Strategy 4: schema default
            if "default" in field_schema:
                filled_inputs[field_name] = field_schema["default"]
                continue

            # Strategy 5: missing required
            if field_name in required_fields:
                missing_required.append(field_name)

        return IOResolutionResult(
            capability_id=capability["capability_id"],
            capability_type=capability["type"],
            capability_name=capability["name"],
            input_schema=input_schema,
            filled_inputs=filled_inputs,
            missing_required_inputs=missing_required,
            output_schema=self._preserve_output_schema(
                capability.get("output_schema") or {}
            ),
            data_dependencies=data_dependencies,
            field_mappings=field_mappings,
            detected_prerequisites=detected_prerequisites,
        )

    async def _extract_from_query(
        self,
        user_query: str,
        input_schema: dict[str, Any],
        task_description: str,
        model: str | None = None,
    ) -> dict[str, Any]:
        """
        Use LLM to extract structured input values from the natural language query.

        Returns a dict of field_name → extracted_value (None for unextractable fields).
        """
        prompt = INPUT_EXTRACTION_PROMPT.format(
            user_query=user_query,
            task_description=task_description,
            input_schema=json.dumps(input_schema, indent=2),
        )

        try:
            response = await self._llm.complete(
                model=model or "",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0,
            )
            data = json.loads(response)
            return data.get("extracted_inputs", {})
        except (json.JSONDecodeError, Exception) as exc:
            logger.warning("Input extraction LLM call failed: %s", exc)
            return {}

    async def _find_providing_task(
        self,
        field_name: str,
        field_schema: dict[str, Any],
        previous_tasks: list[dict[str, Any]],
        model: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Find which previous task can provide this input field via semantic matching.

        Tasks use different field names for semantically equivalent data (e.g.
        "cost" vs "price" vs "amount").  We use an LLM to match by meaning, not
        by exact name.  A high confidence threshold (0.85) prevents cross-domain
        hallucinations such as matching "hotel_id" to "cheapest_price".

        Returns a dict with keys: task, output_field, confidence, reasoning
        or None if no suitable match is found.
        """
        if not previous_tasks:
            return None

        # Deduplicate tasks so the LLM doesn't see identical output fields twice
        deduped_tasks = self._deduplicate_previous_tasks(previous_tasks)

        # Build candidate list from output schemas of resolved previous tasks.
        # Only include fields whose base type is compatible with the required
        # input field — this prevents cross-type hallucinations (e.g. LLM
        # matching a string date field to a numeric price field at 0.95).
        candidates: list[dict[str, Any]] = []
        for task in reversed(deduped_tasks):  # most-recent first
            capability = task.get("capability")
            if not capability:
                continue
            output_schema = capability.get("output_schema", {})
            output_props: dict[str, Any] = output_schema.get("properties", {})
            for output_field_name, output_field_schema in output_props.items():
                if not self._types_strictly_compatible(
                    field_schema, output_field_schema
                ):
                    logger.debug(
                        "Pre-filter: skipping '%s.%s' (%s) — type incompatible with '%s' (%s)",
                        task["id"],
                        output_field_name,
                        output_field_schema.get("type", "?"),
                        field_name,
                        field_schema.get("type", "?"),
                    )
                    continue
                candidates.append(
                    {
                        "task_id": task["id"],
                        "task_description": task.get("task", {}).get(
                            "description", task.get("description", "")
                        ),
                        "field_name": output_field_name,
                        "field_schema": output_field_schema,  # kept for post-LLM check
                        "field_type": output_field_schema.get("type", ""),
                        "field_description": output_field_schema.get("description", ""),
                        "enum_values": output_field_schema.get("enum", []),
                    }
                )

        if not candidates:
            return None

        # Strip the internal field_schema key before building the LLM prompt
        prompt_candidates = [
            {k: v for k, v in c.items() if k != "field_schema"} for c in candidates
        ]
        prompt = FIELD_MATCHING_PROMPT.format(
            field_name=field_name,
            field_type=field_schema.get("type", ""),
            field_description=field_schema.get("description", "N/A"),
            candidates_json=json.dumps(prompt_candidates, indent=2),
        )

        logger.debug(
            "Running field matching for '%s' with prompt:\n%s", field_name, prompt
        )

        try:
            response = await self._llm.complete(
                model=self._model or "",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0,
            )
            match_result = json.loads(response)
            logger.debug(
                "llm response to field matching for field '%s': %s",
                field_name,
                match_result,
            )
        except (json.JSONDecodeError, Exception) as exc:
            logger.warning(
                "Field matching LLM call failed for field %r: %s", field_name, exc
            )
            return None

        confidence = match_result.get("confidence", 0)
        matched_task_id = match_result.get("matched_task_id")
        matched_field_name = match_result.get("matched_field_name", "")
        if confidence < _FIELD_MATCH_CONFIDENCE or not matched_task_id:
            return None

        # Post-LLM type guard: re-verify that the matched field's schema is
        # actually type-compatible even though we pre-filtered.  The LLM
        # sometimes picks a field from its training knowledge that wasn't in
        # the filtered candidate list.
        matched_candidate_schema = next(
            (
                c["field_schema"]
                for c in candidates
                if c["field_name"] == matched_field_name
            ),
            {},
        )
        if matched_candidate_schema and not self._types_strictly_compatible(
            field_schema, matched_candidate_schema
        ):
            logger.warning(
                "Post-LLM type guard: rejecting match '%s' → '%s.%s' "
                "(input type=%s, output type=%s, confidence=%.2f)",
                field_name,
                matched_task_id,
                matched_field_name,
                field_schema.get("type", "?"),
                matched_candidate_schema.get("type", "?"),
                confidence,
            )
            return None

        # Find the matched task object
        for task in previous_tasks:
            if task["id"] == matched_task_id:
                return {
                    "task": task,
                    "output_field": matched_field_name,
                    "confidence": confidence,
                    "reasoning": match_result.get("reasoning", ""),
                }

        return None

    # ------------------------------------------------------------------
    # Prerequisite detection and insertion
    # ------------------------------------------------------------------

    async def _detect_missing_prerequisite(
        self,
        field_name: str,
        field_schema: dict[str, Any],
        task_description: str,
        previous_tasks: list[dict[str, Any]],
        model: str | None = None,
    ) -> PrerequisiteInfo | None:
        """
        Ask the LLM whether a missing upstream task would naturally produce
        *field_name* as output.

        Returns a PrerequisiteInfo when a prerequisite is identified, None otherwise.
        """
        # Summarise previous tasks for the prompt (descriptions + output field names)
        prev_summaries = []
        for t in previous_tasks:
            cap = t.get("capability", {})
            output_fields = list(
                cap.get("output_schema", {}).get("properties", {}).keys()
            )
            prev_summaries.append(
                {
                    "id": t.get("id", ""),
                    "description": t.get("task", {}).get(
                        "description", t.get("description", "")
                    ),
                    "output_fields": output_fields,
                }
            )

        prompt = PREREQUISITE_DETECTION_PROMPT.format(
            task_description=task_description,
            field_name=field_name,
            field_type=field_schema.get("type", ""),
            field_description=field_schema.get("description", "N/A"),
            previous_tasks_json=json.dumps(prev_summaries, indent=2),
        )

        logger.debug(
            "Running prerequisite detection for field '%s' with prompt:\n%s",
            field_name,
            prompt,
        )

        try:
            response = await self._llm.complete(
                model=model or self._model or "",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0,
            )
            result = json.loads(response)
            logger.debug(
                "llm response to detecing prerequisite for field '%s': %s",
                field_name,
                result,
            )

        except (json.JSONDecodeError, Exception) as exc:
            logger.warning(
                "Prerequisite detection LLM call failed for field %r: %s",
                field_name,
                exc,
            )
            return None

        if not result.get("needs_prerequisite"):
            return None

        action = result.get("action_description") or ""
        hint = result.get("capability_hint") or ""
        if not action:
            return None

        logger.debug(
            "Prerequisite detected for field '%s': action='%s' hint='%s'",
            field_name,
            action,
            hint,
        )
        return PrerequisiteInfo(
            field_name=field_name,
            action_description=action,
            capability_hint=hint,
        )

    async def _create_prerequisite_task(
        self,
        prereq: PrerequisiteInfo,
        parent_task: dict[str, Any],
        previous_tasks: list[dict[str, Any]],
        user_query: str,
        model: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Search for an agent that can fulfil the prerequisite, run IO resolution
        on it (depth=1, no further prerequisite expansion), and return the fully
        resolved task dict ready for insertion into the workflow.

        Returns None if no suitable agent is found.
        """
        if self._search_pipeline is None or self._coverage_analyzer is None:
            return None

        prereq_id = f"prereq_{prereq.field_name}_{parent_task.get('id', 'unknown')}"
        search_query = prereq.action_description

        try:
            candidates = await self._search_pipeline.search(search_query)
        except Exception as exc:
            logger.warning(
                "Agent search failed for prerequisite '%s': %s", search_query, exc
            )
            return None

        if not candidates:
            logger.info(
                "No agents found for prerequisite '%s' (field: %s)",
                search_query,
                prereq.field_name,
            )
            return None

        prereq_task_stub = {
            "id": prereq_id,
            "type": "agent_task",
            "description": prereq.action_description,
            "depends_on": [],
        }

        try:
            coverage = await self._coverage_analyzer.analyze_coverage(
                prereq_task_stub, candidates
            )
        except Exception as exc:
            logger.warning(
                "Coverage analysis failed for prerequisite '%s': %s", search_query, exc
            )
            return None

        if coverage.strategy == "single_agent" and coverage.agent:
            agent = coverage.agent
        elif coverage.strategy == "sequential_chain" and coverage.chain:
            agent = coverage.chain[0]
        elif coverage.available_agents:
            agent = coverage.available_agents[0]
        else:
            logger.info("No coverage found for prerequisite '%s'", search_query)
            return None

        prereq_task_stub["agent_id"] = agent.agent_id
        prereq_task_stub["agent_manifest"] = agent.manifest

        # Run IO resolution with depth=1 (no recursive prereq detection).
        # We temporarily disable search_pipeline to prevent recursion.
        try:
            capability = await self._select_capability(
                task=prereq_task_stub,
                agent_manifest=agent.manifest,
                model=model,
            )
            io_result = await self._resolve_inputs_no_prereq(
                task=prereq_task_stub,
                capability=capability,
                user_query=user_query,
                previous_tasks=previous_tasks,
                model=model,
            )
        except Exception as exc:
            logger.warning(
                "IO resolution failed for prerequisite task '%s': %s", prereq_id, exc
            )
            return None

        resolved = self._create_resolved_task(prereq_task_stub, io_result)
        logger.debug(
            "Created prerequisite task '%s' for field '%s'",
            prereq_id,
            prereq.field_name,
        )
        return resolved

    async def _resolve_inputs_no_prereq(
        self,
        task: dict[str, Any],
        capability: dict[str, Any],
        user_query: str,
        previous_tasks: list[dict[str, Any]],
        model: str | None = None,
    ) -> IOResolutionResult:
        """
        Simplified version of _resolve_inputs that skips prerequisite detection
        (Strategy 3) to avoid infinite recursion when resolving an already-inserted
        prerequisite task.
        """
        input_schema = capability.get("input_schema") or {}
        properties: dict[str, Any] = input_schema.get("properties", {})
        required_fields: list[str] = input_schema.get("required", [])

        extracted_from_query = await self._extract_from_query(
            user_query=user_query,
            input_schema=input_schema,
            task_description=task.get("description", ""),
            model=model,
        )

        filled_inputs: dict[str, Any] = {}
        missing_required: list[str] = []
        data_dependencies: list[str] = []
        field_mappings: list[dict[str, Any]] = []

        for field_name, field_schema in properties.items():
            extracted_value = extracted_from_query.get(field_name)
            if extracted_value is not None:
                filled_inputs[field_name] = extracted_value
                continue

            providing_info = await self._find_providing_task(
                field_name=field_name,
                field_schema=field_schema,
                previous_tasks=previous_tasks,
                model=model,
            )
            if providing_info:
                providing_task = providing_info["task"]
                output_field = providing_info["output_field"]
                filled_inputs[field_name] = (
                    f"$tasks.{providing_task['id']}.output.{output_field}"
                )
                dep_id = providing_task["id"]
                if dep_id not in data_dependencies:
                    data_dependencies.append(dep_id)
                field_mappings.append(
                    {
                        "source_task": dep_id,
                        "source_field": output_field,
                        "target_field": field_name,
                        "confidence": providing_info["confidence"],
                        "reasoning": providing_info.get("reasoning", ""),
                    }
                )
                continue

            if "default" in field_schema:
                filled_inputs[field_name] = field_schema["default"]
                continue

            if field_name in required_fields:
                missing_required.append(field_name)

        return IOResolutionResult(
            capability_id=capability["capability_id"],
            capability_type=capability["type"],
            capability_name=capability["name"],
            input_schema=input_schema,
            filled_inputs=filled_inputs,
            missing_required_inputs=missing_required,
            output_schema=self._preserve_output_schema(
                capability.get("output_schema") or {}
            ),
            data_dependencies=data_dependencies,
            field_mappings=field_mappings,
        )

    # ------------------------------------------------------------------
    # Task assembly helpers
    # ------------------------------------------------------------------

    def _preserve_output_schema(self, output_schema: dict[str, Any]) -> dict[str, Any]:
        """Return the output schema as-is for runtime type validation."""
        return output_schema

    def _create_resolved_task(
        self,
        original_task: dict[str, Any],
        io_result: IOResolutionResult,
    ) -> dict[str, Any]:
        """
        Build the enriched task dict from the original task + IO resolution result.

        The returned dict drives the node builder in pipeline.py.
        """
        # Merge data_dependencies with the task's existing depends_on list
        existing_deps: list[str] = list(original_task.get("depends_on", []))
        for dep in io_result.data_dependencies:
            if dep not in existing_deps:
                existing_deps.append(dep)

        return {
            "id": original_task["id"],
            "type": "standard",
            "agent_id": original_task.get("agent_id", ""),
            # Capability block with real schemas from agent manifest
            "capability": {
                "capability_id": io_result.capability_id,
                "type": io_result.capability_type,
                "name": io_result.capability_name,
                "input_schema": io_result.input_schema,
                "output_schema": io_result.output_schema,
            },
            # Task descriptor with resolved inputs
            "task": {
                "description": original_task.get("description", ""),
                "inputs": io_result.filled_inputs,
                "unresolved_inputs": io_result.missing_required_inputs,
            },
            "depends_on": existing_deps,
            "unresolved_inputs": io_result.missing_required_inputs,
            "field_mappings": io_result.field_mappings,
            # Carry through metadata the pipeline may need
            "agent_manifest": original_task.get("agent_manifest"),
            "coverage_strategy": original_task.get("coverage_strategy", "single_agent"),
            "orchestration_hint": original_task.get("orchestration_hint"),
        }

    def _create_hitl_node(
        self,
        all_missing_inputs: dict[str, list[str]],
    ) -> dict[str, Any]:
        """
        Create a human-in-the-loop system_tool node that collects all missing inputs.

        This node is prepended to the workflow and runs first.  Its outputs
        (collected_inputs) are referenced by downstream tasks at runtime.
        """
        input_requests: list[dict[str, Any]] = []
        for task_id, missing_fields in all_missing_inputs.items():
            for field in missing_fields:
                input_requests.append(
                    {
                        "target_task": task_id,
                        "field_name": field,
                        "prompt": f"Please provide {field} for {task_id}",
                    }
                )

        return {
            "id": "hitl_input_collection",
            "type": "system_tool",
            "tool_name": "human_input",
            "inputs": {
                "requests": input_requests,
            },
            "depends_on": [],
            "outputs": {
                "collected_inputs": {},  # Populated at runtime
            },
        }
