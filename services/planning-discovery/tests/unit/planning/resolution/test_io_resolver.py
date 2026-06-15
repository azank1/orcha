"""Unit tests for IOResolver (Stage 2b)."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from planning_discovery.planning.resolution.io_resolver import (
    _FIELD_MATCH_CONFIDENCE,
    IOResolver,
    PrerequisiteInfo,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------


def _make_llm(
    complete_returns: str = "0", embed_returns: list | None = None
) -> MagicMock:
    """Create a mock LLMProvider."""
    llm = MagicMock()
    llm.complete = AsyncMock(return_value=complete_returns)
    llm.embed = AsyncMock(return_value=embed_returns or [0.1] * 8)
    return llm


def _flight_manifest() -> dict[str, Any]:
    return {
        "id": "did:metaorcha:agent:skylink",
        "name": "Skylink Flight Search",
        "capabilities": [
            {
                "capability_id": "search_flights",
                "type": "TOOL",
                "name": "Search Flights",
                "description": "Search for available flights between airports",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "origin": {"type": "string"},
                        "destination": {"type": "string"},
                        "departure_date": {"type": "string", "format": "date"},
                        "passengers": {"type": "integer", "default": 1},
                    },
                    "required": ["origin", "destination", "departure_date"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "flights": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "flight_id": {"type": "string"},
                                    "price": {"type": "number"},
                                    "arrival_time": {
                                        "type": "string",
                                        "format": "date-time",
                                    },
                                },
                            },
                        },
                        "cheapest_price": {"type": "number"},
                    },
                },
            },
            {
                "capability_id": "book_flight",
                "type": "TOOL",
                "name": "Book Flight",
                "description": "Book a specific flight",
                "input_schema": {
                    "type": "object",
                    "properties": {"flight_id": {"type": "string"}},
                    "required": ["flight_id"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {"booking_id": {"type": "string"}},
                },
            },
        ],
    }


def _flight_task(task_id: str = "task_1") -> dict[str, Any]:
    return {
        "id": task_id,
        "type": "agent_task",
        "description": "Find flights from London to Tokyo on March 15th for 2 passengers",
        "depends_on": [],
        "inputs": {},
        "agent_id": "did:metaorcha:agent:skylink",
        "agent_manifest": _flight_manifest(),
    }


# ---------------------------------------------------------------------------
# Capability selection
# ---------------------------------------------------------------------------


class TestCapabilitySelection:
    """Tests for _select_capability."""

    @pytest.mark.asyncio
    async def test_selects_by_llm_index(self) -> None:
        """LLM returning index 0 picks the first capability."""
        llm = _make_llm(complete_returns="0")
        resolver = IOResolver(llm)
        task = _flight_task()
        cap = await resolver._select_capability(task, _flight_manifest())
        assert cap["capability_id"] == "search_flights"

    @pytest.mark.asyncio
    async def test_selects_second_capability(self) -> None:
        """LLM returning index 1 picks the second capability."""
        llm = _make_llm(complete_returns="1")
        resolver = IOResolver(llm)
        task = _flight_task()
        task["description"] = "Book a specific flight"
        cap = await resolver._select_capability(task, _flight_manifest())
        assert cap["capability_id"] == "book_flight"

    @pytest.mark.asyncio
    async def test_single_capability_skips_llm(self) -> None:
        """When only one capability exists the LLM is not called."""
        llm = _make_llm()
        resolver = IOResolver(llm)
        manifest = dict(_flight_manifest())
        manifest["capabilities"] = [_flight_manifest()["capabilities"][0]]
        task = _flight_task()
        cap = await resolver._select_capability(task, manifest)
        llm.complete.assert_not_awaited()
        assert cap["capability_id"] == "search_flights"

    @pytest.mark.asyncio
    async def test_invalid_llm_index_defaults_to_zero(self) -> None:
        """Non-integer LLM response defaults to capability 0."""
        llm = _make_llm(complete_returns="not_an_int")
        resolver = IOResolver(llm)
        cap = await resolver._select_capability(_flight_task(), _flight_manifest())
        assert cap["capability_id"] == "search_flights"

    @pytest.mark.asyncio
    async def test_raises_on_empty_capabilities(self) -> None:
        """Agent with no capabilities raises ValueError."""
        llm = _make_llm()
        resolver = IOResolver(llm)
        manifest = {"id": "agent_x", "capabilities": []}
        with pytest.raises(ValueError, match="no capabilities"):
            await resolver._select_capability(_flight_task(), manifest)


# ---------------------------------------------------------------------------
# Input extraction from query
# ---------------------------------------------------------------------------


class TestInputExtraction:
    """Tests for _extract_from_query."""

    @pytest.mark.asyncio
    async def test_extracts_values_from_query(self) -> None:
        """LLM correctly extracts structured values from natural language."""
        llm = _make_llm(
            complete_returns=json.dumps(
                {
                    "extracted_inputs": {
                        "origin": "LHR",
                        "destination": "NRT",
                        "departure_date": "2026-03-15",
                        "passengers": 2,
                    }
                }
            )
        )
        resolver = IOResolver(llm)
        input_schema = {
            "properties": {
                "origin": {"type": "string"},
                "destination": {"type": "string"},
                "departure_date": {"type": "string"},
                "passengers": {"type": "integer"},
            }
        }
        result = await resolver._extract_from_query(
            user_query="Find flights from LHR to NRT on 2026-03-15 for 2 passengers",
            input_schema=input_schema,
            task_description="Search flights",
        )
        assert result["origin"] == "LHR"
        assert result["destination"] == "NRT"
        assert result["departure_date"] == "2026-03-15"
        assert result["passengers"] == 2

    @pytest.mark.asyncio
    async def test_null_for_unmentioned_fields(self) -> None:
        """Fields not mentioned in the query are returned as null/None."""
        llm = _make_llm(
            complete_returns=json.dumps(
                {
                    "extracted_inputs": {
                        "location": "Shibuya",
                        "check_in_date": None,
                        "num_nights": None,
                    }
                }
            )
        )
        resolver = IOResolver(llm)
        input_schema = {
            "properties": {"location": {}, "check_in_date": {}, "num_nights": {}}
        }
        result = await resolver._extract_from_query(
            user_query="Book a hotel in Shibuya",
            input_schema=input_schema,
            task_description="Book hotel",
        )
        assert result["location"] == "Shibuya"
        assert result["check_in_date"] is None
        assert result["num_nights"] is None

    @pytest.mark.asyncio
    async def test_returns_empty_dict_on_llm_failure(self) -> None:
        """Malformed LLM response returns empty dict gracefully."""
        llm = _make_llm(complete_returns="not json at all")
        resolver = IOResolver(llm)
        result = await resolver._extract_from_query("query", {}, "task")
        assert result == {}


# ---------------------------------------------------------------------------
# Missing required input detection & HITL node creation
# ---------------------------------------------------------------------------


class TestMissingInputs:
    """Tests for missing required input detection."""

    @pytest.mark.asyncio
    async def test_missing_required_field_detected(self) -> None:
        """Required fields not in query and not resolvable from prior tasks are flagged."""
        # LLM returns origin and destination but not departure_date
        llm = _make_llm(
            complete_returns=json.dumps(
                {
                    "extracted_inputs": {
                        "origin": "London",
                        "destination": "Tokyo",
                        "departure_date": None,
                    }
                }
            )
        )
        # Second call for field matching: no match
        llm.complete = AsyncMock(
            side_effect=[
                json.dumps(
                    {
                        "extracted_inputs": {
                            "origin": "London",
                            "destination": "Tokyo",
                            "departure_date": None,
                        }
                    }
                ),
                json.dumps(
                    {
                        "matched_task_id": None,
                        "matched_field_name": None,
                        "confidence": 0.1,
                        "reasoning": "",
                    }
                ),
            ]
        )
        resolver = IOResolver(llm)
        capability = _flight_manifest()["capabilities"][0]
        result = await resolver._resolve_inputs(
            task=_flight_task(),
            capability=capability,
            user_query="Book a flight to Tokyo",
            previous_tasks=[],
        )
        assert "departure_date" in result.missing_required_inputs

    @pytest.mark.asyncio
    async def test_default_value_fills_optional_field(self) -> None:
        """Fields with defaults in the schema are filled without LLM."""
        llm = _make_llm(
            complete_returns=json.dumps(
                {
                    "extracted_inputs": {
                        "origin": "London",
                        "destination": "Tokyo",
                        "departure_date": "2026-03-15",
                        "passengers": None,
                    }
                }
            )
        )
        resolver = IOResolver(llm)
        capability = _flight_manifest()["capabilities"][0]
        result = await resolver._resolve_inputs(
            task=_flight_task(),
            capability=capability,
            user_query="Find flights from London to Tokyo on March 15th",
            previous_tasks=[],
        )
        # 'passengers' has default=1 in the schema
        assert result.filled_inputs.get("passengers") == 1
        assert "passengers" not in result.missing_required_inputs


class TestHITLNode:
    """Tests for HITL node creation."""

    def test_creates_hitl_node_with_requests(self) -> None:
        resolver = IOResolver(_make_llm())
        missing = {
            "task_2": ["departure_date", "passengers"],
            "task_3": ["check_in_date"],
        }
        hitl = resolver._create_hitl_node(missing)
        assert hitl["id"] == "hitl_input_collection"
        assert hitl["type"] == "system_tool"
        assert hitl["tool_name"] == "human_input"
        requests = hitl["inputs"]["requests"]
        assert len(requests) == 3
        target_tasks = {r["target_task"] for r in requests}
        assert "task_2" in target_tasks
        assert "task_3" in target_tasks

    def test_no_hitl_when_all_inputs_satisfied(self) -> None:
        """resolve_io returns hitl_node=None when all required inputs are filled."""
        resolver = IOResolver(_make_llm())
        hitl = resolver._create_hitl_node({})  # empty dict = no missing inputs
        assert hitl["inputs"]["requests"] == []


# ---------------------------------------------------------------------------
# Semantic field matching — confidence threshold and null returns
# ---------------------------------------------------------------------------


class TestFieldMatching:
    """Tests for _find_providing_task and the confidence threshold."""

    def test_confidence_threshold_is_high(self) -> None:
        """The module-level threshold is set to 0.85 (not 0.7)."""
        assert _FIELD_MATCH_CONFIDENCE == 0.85

    @pytest.mark.asyncio
    async def test_returns_none_when_confidence_below_threshold(self) -> None:
        """Low-confidence match (cross-domain hallucination) is rejected."""
        llm = _make_llm(
            complete_returns=json.dumps(
                {
                    "matched_task_id": "task_1",
                    "matched_field_name": "cheapest_price",
                    "confidence": 0.6,  # below 0.85 threshold
                    "reasoning": "price is vaguely related to hotel_id",
                }
            )
        )
        resolver = IOResolver(llm)

        previous_flight_task = {
            "id": "task_1",
            "type": "standard",
            "task": {"description": "Search flights"},
            "capability": {
                "output_schema": {
                    "properties": {
                        "cheapest_price": {
                            "type": "number",
                            "description": "Cheapest available price",
                        },
                        "flights": {"type": "array"},
                    }
                }
            },
        }

        result = await resolver._find_providing_task(
            field_name="hotel_id",
            field_schema={"type": "string", "description": "Unique hotel identifier"},
            previous_tasks=[previous_flight_task],
        )
        assert result is None, "Low-confidence cross-domain match should be rejected"

    @pytest.mark.asyncio
    async def test_returns_none_when_llm_returns_null_match(self) -> None:
        """LLM explicitly returning null matched_task_id is handled gracefully."""
        llm = _make_llm(
            complete_returns=json.dumps(
                {
                    "matched_task_id": None,
                    "matched_field_name": None,
                    "confidence": 0.0,
                    "reasoning": "hotel_id has no semantic match in flight search outputs",
                }
            )
        )
        resolver = IOResolver(llm)

        previous_flight_task = {
            "id": "task_1",
            "type": "standard",
            "task": {"description": "Search flights"},
            "capability": {
                "output_schema": {"properties": {"cheapest_price": {"type": "number"}}}
            },
        }

        result = await resolver._find_providing_task(
            field_name="hotel_id",
            field_schema={"type": "string"},
            previous_tasks=[previous_flight_task],
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_match_above_threshold(self) -> None:
        """Match at or above 0.85 confidence is accepted."""
        llm = _make_llm(
            complete_returns=json.dumps(
                {
                    "matched_task_id": "task_1",
                    "matched_field_name": "arrival_time",
                    "confidence": 0.91,
                    "reasoning": "flight arrival time semantically matches hotel check-in date",
                }
            )
        )
        resolver = IOResolver(llm)

        previous_task = {
            "id": "task_1",
            "type": "standard",
            "task": {"description": "Search flights"},
            "capability": {
                "output_schema": {
                    "properties": {
                        "arrival_time": {"type": "string", "format": "date-time"},
                    }
                }
            },
        }

        result = await resolver._find_providing_task(
            field_name="check_in_date",
            field_schema={"type": "string", "format": "date"},
            previous_tasks=[previous_task],
        )
        assert result is not None
        assert result["output_field"] == "arrival_time"
        assert result["confidence"] == 0.91

    @pytest.mark.asyncio
    async def test_returns_none_when_no_previous_tasks(self) -> None:
        """No previous tasks → no candidates → immediately returns None."""
        resolver = IOResolver(_make_llm())
        result = await resolver._find_providing_task("hotel_id", {}, [])
        assert result is None


# ---------------------------------------------------------------------------
# Prerequisite detection
# ---------------------------------------------------------------------------


class TestPrerequisiteDetection:
    """Tests for _detect_missing_prerequisite."""

    @pytest.mark.asyncio
    async def test_returns_prerequisite_info_when_needed(self) -> None:
        """LLM says needs_prerequisite=true → PrerequisiteInfo is returned."""
        llm = _make_llm(
            complete_returns=json.dumps(
                {
                    "needs_prerequisite": True,
                    "action_description": "search hotels in Tokyo",
                    "capability_hint": "hotel search",
                    "reasoning": "Booking requires a hotel search step to obtain hotel_id",
                }
            )
        )
        resolver = IOResolver(llm)

        result = await resolver._detect_missing_prerequisite(
            field_name="hotel_id",
            field_schema={"type": "string", "description": "Hotel identifier"},
            task_description="Book a hotel in Tokyo",
            previous_tasks=[],
        )

        assert result is not None
        assert isinstance(result, PrerequisiteInfo)
        assert result.field_name == "hotel_id"
        assert "hotel" in result.action_description.lower()
        assert result.capability_hint == "hotel search"

    @pytest.mark.asyncio
    async def test_returns_none_when_no_prerequisite_needed(self) -> None:
        """LLM says needs_prerequisite=false → None returned (field goes to HITL)."""
        llm = _make_llm(
            complete_returns=json.dumps(
                {
                    "needs_prerequisite": False,
                    "action_description": None,
                    "capability_hint": None,
                    "reasoning": "guest_name is personal info that must come from the user",
                }
            )
        )
        resolver = IOResolver(llm)

        result = await resolver._detect_missing_prerequisite(
            field_name="guest_name",
            field_schema={"type": "string", "description": "Primary guest full name"},
            task_description="Book a hotel in Tokyo",
            previous_tasks=[],
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_llm_failure(self) -> None:
        """Bad LLM response is handled gracefully — returns None."""
        llm = _make_llm(complete_returns="not json")
        resolver = IOResolver(llm)

        result = await resolver._detect_missing_prerequisite(
            field_name="hotel_id",
            field_schema={},
            task_description="Book hotel",
            previous_tasks=[],
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_prerequisite_not_triggered_without_search_pipeline(self) -> None:
        """When no search_pipeline injected, prerequisite detection is skipped entirely."""
        llm = _make_llm()
        # LLM side-effects: extraction returns null for hotel_id.
        # No field-matching call because previous_tasks=[] → _find_providing_task returns
        # None immediately without calling the LLM.
        llm.complete = AsyncMock(
            side_effect=[
                json.dumps({"extracted_inputs": {"hotel_id": None}}),
            ]
        )
        # No search_pipeline → resolver should NOT call LLM for prerequisite detection
        resolver = IOResolver(llm, search_pipeline=None, coverage_analyzer=None)

        capability = {
            "capability_id": "book_hotel",
            "type": "TOOL",
            "name": "Book Hotel",
            "input_schema": {
                "type": "object",
                "properties": {"hotel_id": {"type": "string"}},
                "required": ["hotel_id"],
            },
            "output_schema": {},
        }
        result = await resolver._resolve_inputs(
            task={"id": "task_2", "description": "Book hotel"},
            capability=capability,
            user_query="Book a hotel in Tokyo",
            previous_tasks=[],
        )
        # hotel_id is missing — no prerequisite was inserted
        assert "hotel_id" in result.missing_required_inputs
        assert result.detected_prerequisites == []
        # LLM called exactly once (extraction only) — field matching skipped (no prev tasks),
        # prereq detection skipped (no search_pipeline)
        assert llm.complete.call_count == 1


# ---------------------------------------------------------------------------
# Prerequisite insertion in resolve_io
# ---------------------------------------------------------------------------


class TestPrerequisiteInsertion:
    """Tests for the full prerequisite insert loop in resolve_io."""

    @pytest.mark.asyncio
    async def test_prerequisite_task_inserted_and_field_wired(self) -> None:
        """
        When a prerequisite is detected and an agent is found, a new task
        is inserted and the original task's input is wired via $tasks.*.
        """
        # Build mock search_pipeline that returns one fake agent candidate
        mock_agent = MagicMock()
        mock_agent.agent_id = "did:metaorcha:agent:hotel-search"
        mock_agent.manifest = {
            "id": "did:metaorcha:agent:hotel-search",
            "name": "Hotel Search",
            "capabilities": [
                {
                    "capability_id": "find_hotels",
                    "type": "TOOL",
                    "name": "Find Hotels",
                    "description": "Search for hotels",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "destination": {"type": "string"},
                        },
                        "required": ["destination"],
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "accommodation_id": {
                                "type": "string",
                                "description": "Unique identifier for the selected accommodation",
                            },
                            "property_name": {"type": "string"},
                        },
                    },
                }
            ],
        }

        mock_coverage = MagicMock()
        mock_coverage.strategy = "single_agent"
        mock_coverage.agent = mock_agent

        search_pipeline = MagicMock()
        search_pipeline.search = AsyncMock(return_value=[mock_agent])
        coverage_analyzer = MagicMock()
        coverage_analyzer.analyze_coverage = AsyncMock(return_value=mock_coverage)

        # LLM call sequence:
        # Both manifests have exactly 1 capability each → capability selection never calls LLM.
        # _find_providing_task with no previous tasks returns None without LLM call.
        #
        # 1. Input extraction for booking task → hotel_id=None, check_in="2026-03-15"
        # 2. Prerequisite detection for hotel_id → needs_prerequisite=True
        # 3. Input extraction for prereq task → destination="Tokyo"
        #    (no field matching for prereq: no previous tasks when resolving it)
        # 4. Re-run field matching for hotel_id with prereq now in scope
        llm = _make_llm()
        llm.complete = AsyncMock(
            side_effect=[
                json.dumps(
                    {"extracted_inputs": {"hotel_id": None, "check_in": "2026-03-15"}}
                ),
                json.dumps(
                    {
                        "needs_prerequisite": True,
                        "action_description": "search hotels in Tokyo",
                        "capability_hint": "hotel search",
                        "reasoning": "Need to search first",
                    }
                ),
                json.dumps({"extracted_inputs": {"destination": "Tokyo"}}),
                # Re-run field matching for hotel_id after prereq inserted
                json.dumps(
                    {
                        "matched_task_id": "prereq_hotel_id_task_book",
                        "matched_field_name": "accommodation_id",
                        "confidence": 0.92,
                        "reasoning": "accommodation_id semantically matches hotel_id",
                    }
                ),
            ]
        )

        resolver = IOResolver(
            llm,
            search_pipeline=search_pipeline,
            coverage_analyzer=coverage_analyzer,
        )

        booking_task = {
            "id": "task_book",
            "type": "agent_task",
            "description": "Book a hotel in Tokyo",
            "depends_on": [],
            "agent_id": "did:metaorcha:agent:staywise",
            "agent_manifest": {
                "id": "did:metaorcha:agent:staywise",
                "name": "StayWise",
                "capabilities": [
                    {
                        "capability_id": "book_hotel",
                        "type": "TOOL",
                        "name": "Book Hotel",
                        "description": "Book a hotel",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "hotel_id": {
                                    "type": "string",
                                    "description": "Hotel identifier from search",
                                },
                                "check_in": {"type": "string", "format": "date"},
                            },
                            "required": ["hotel_id", "check_in"],
                        },
                        "output_schema": {
                            "type": "object",
                            "properties": {"booking_ref": {"type": "string"}},
                        },
                    }
                ],
            },
        }

        resolved_tasks, hitl = await resolver.resolve_io(
            tasks=[booking_task],
            user_query="Book a hotel in Tokyo for March 15th",
        )

        # A prerequisite task should have been inserted before the booking task
        assert len(resolved_tasks) == 2, (
            f"Expected 2 tasks (prereq + booking), got {len(resolved_tasks)}"
        )
        prereq_task = resolved_tasks[0]
        booking_resolved = resolved_tasks[1]

        assert prereq_task["id"].startswith("prereq_hotel_id_")
        assert booking_resolved["id"] == "task_book"

        # The booking task's hotel_id input should be a $tasks.* reference to the prereq
        hotel_id_value = booking_resolved["task"]["inputs"].get("hotel_id", "")
        assert "$tasks." in hotel_id_value, (
            f"Expected data reference, got: {hotel_id_value}"
        )
        assert "accommodation_id" in hotel_id_value

        # hitl should be None (hotel_id was resolved; check_in came from query)
        assert hitl is None


# ---------------------------------------------------------------------------
# Data reference creation
# ---------------------------------------------------------------------------


class TestDataReferences:
    """Tests for $tasks data references between task outputs and inputs."""

    @pytest.mark.asyncio
    async def test_data_reference_format(self) -> None:
        """When a field is resolved from a previous task, input uses $tasks.xxx format."""
        llm = _make_llm()
        llm.complete = AsyncMock(
            side_effect=[
                # Input extraction — check_in_date not in query
                json.dumps(
                    {
                        "extracted_inputs": {
                            "location": "Shibuya",
                            "check_in_date": None,
                            "num_nights": None,
                        }
                    }
                ),
                # Field matching for check_in_date — match found in task_1 (confidence ≥ 0.85)
                json.dumps(
                    {
                        "matched_task_id": "task_1",
                        "matched_field_name": "arrival_time",
                        "confidence": 0.92,
                        "reasoning": "Flight arrival time semantically matches hotel check-in date",
                    }
                ),
                # Field matching for num_nights — no match
                json.dumps(
                    {
                        "matched_task_id": None,
                        "matched_field_name": None,
                        "confidence": 0.1,
                        "reasoning": "",
                    }
                ),
            ]
        )
        resolver = IOResolver(llm)

        # task_1 is a previously resolved flight task with output schema.
        # arrival_time is exposed as a top-level date-time field so the type
        # pre-filter recognises it as date-compatible with check_in_date (date).
        previous_task = {
            "id": "task_1",
            "type": "standard",
            "task": {"description": "Search flights", "inputs": {}},
            "capability": {
                "output_schema": {
                    "properties": {
                        "arrival_time": {"type": "string", "format": "date-time"},
                    }
                }
            },
        }

        hotel_capability = {
            "capability_id": "book_hotel",
            "type": "TOOL",
            "name": "Book Hotel",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "check_in_date": {"type": "string", "format": "date"},
                    "num_nights": {"type": "integer"},
                },
                "required": ["location", "check_in_date", "num_nights"],
            },
            "output_schema": {"type": "object", "properties": {}},
        }

        result = await resolver._resolve_inputs(
            task={"id": "task_2", "description": "Book hotel in Shibuya"},
            capability=hotel_capability,
            user_query="Book a hotel in Shibuya",
            previous_tasks=[previous_task],
        )

        assert result.filled_inputs.get("location") == "Shibuya"
        # check_in_date resolved via semantic match to task_1 output
        assert "$tasks.task_1" in result.filled_inputs.get("check_in_date", "")
        assert "task_1" in result.data_dependencies
        # num_nights is missing (required, no match)
        assert "num_nights" in result.missing_required_inputs


# ---------------------------------------------------------------------------
# resolve_io integration
# ---------------------------------------------------------------------------


class TestResolveIO:
    """Integration-level tests for the full resolve_io() method."""

    @pytest.mark.asyncio
    async def test_non_agent_tasks_passed_through(self) -> None:
        """Router and system_tool tasks are not IO-resolved, just passed through."""
        llm = _make_llm()
        resolver = IOResolver(llm)
        router_task = {
            "id": "router_1",
            "type": "router",
            "description": "Route based on price",
            "depends_on": [],
        }
        resolved, hitl = await resolver.resolve_io([router_task], "some query")
        assert len(resolved) == 1
        assert resolved[0]["id"] == "router_1"
        assert hitl is None

    @pytest.mark.asyncio
    async def test_tasks_without_manifest_passed_through(self) -> None:
        """Agent tasks without an agent_manifest are passed through unchanged."""
        llm = _make_llm()
        resolver = IOResolver(llm)
        task = {
            "id": "task_1",
            "type": "agent_task",
            "description": "Do something",
            "depends_on": [],
        }
        resolved, hitl = await resolver.resolve_io([task], "query")
        assert resolved[0]["id"] == "task_1"
        # No capability selection attempted since no manifest
        llm.complete.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_hitl_node_created_when_inputs_missing(self) -> None:
        """resolve_io returns a HITL node when required inputs are missing."""
        # LLM: capability selection → 0, extraction → only destination filled
        llm = _make_llm()
        llm.complete = AsyncMock(
            side_effect=[
                "0",  # capability selection
                json.dumps(
                    {
                        "extracted_inputs": {
                            "origin": None,
                            "destination": "Tokyo",
                            "departure_date": None,
                        }
                    }
                ),
                # field matching for origin
                json.dumps(
                    {
                        "matched_task_id": None,
                        "matched_field_name": None,
                        "confidence": 0.0,
                        "reasoning": "",
                    }
                ),
                # field matching for departure_date
                json.dumps(
                    {
                        "matched_task_id": None,
                        "matched_field_name": None,
                        "confidence": 0.0,
                        "reasoning": "",
                    }
                ),
            ]
        )
        resolver = IOResolver(llm)
        task = _flight_task()
        resolved, hitl = await resolver.resolve_io([task], "Book a flight to Tokyo")
        assert hitl is not None
        assert hitl["id"] == "hitl_input_collection"
        missing_fields = {r["field_name"] for r in hitl["inputs"]["requests"]}
        assert "origin" in missing_fields
        assert "departure_date" in missing_fields
