"""Internal data structures used within the planning pipeline.

Combines FZ's pipeline-internal schemas with AZ's telemetry and error models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field

# ═══════════════════════════════════════════════════════════════════════════════
# Task Decomposition (FZ's DecompositionResult + AZ's Task)
# ═══════════════════════════════════════════════════════════════════════════════


class Task(BaseModel):
    """Intermediate task representation from Stage 1 decomposition."""

    id: str
    type: Literal["agent_task", "router", "system_tool"]
    description: str
    intent: str | None = None
    required_capabilities: dict[str, Any] = Field(default_factory=dict)
    inputs: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    expected_output_schema: dict[str, Any] = Field(default_factory=dict)


class DecompositionResult(BaseModel):
    """Full result of the decomposition stage."""

    success: bool
    tasks: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    metadata: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.8
    method: Literal["skip", "single_pass_7b", "fallback_gpt4"] = "single_pass_7b"
    llm_calls: int = 0
    processing_time_ms: float = 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# Agent Resolution (FZ's search result + coverage)
# ═══════════════════════════════════════════════════════════════════════════════


class AgentSearchResult(BaseModel):
    """A single agent candidate returned by the hybrid search."""

    agent_id: str
    name: str = ""
    similarity_score: float = 0.0
    cross_encoder_score: float = 0.0
    confidence: Literal["high", "medium", "low"] = "low"
    capabilities: list[str] = Field(default_factory=list)
    manifest: dict[str, Any] = Field(default_factory=dict)


class CoverageResult(BaseModel):
    """Result of the semantic coverage analysis for a single task."""

    coverage_score: float = 0.0
    strategy: Literal["single_agent", "sequential_chain", "recursive_subgraph"]
    agent: AgentSearchResult | None = None
    chain: list[AgentSearchResult] | None = None
    available_agents: list[AgentSearchResult] | None = None
    matched_agents: list[dict[str, Any]] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    confidence: str = "low"
    coverage_details: dict[str, Any] | None = None
    reasoning: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Validation
# ═══════════════════════════════════════════════════════════════════════════════


class ValidationResult(BaseModel):
    """Result of the tiered validation process."""

    is_valid: bool
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    reasoning: str = ""
    confidence: float = 1.0
    tier: Literal["deterministic", "llm"] = "deterministic"


class ValidationSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """A single validation issue found during verification."""

    rule: str
    severity: ValidationSeverity
    message: str
    node_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationResult:
    """Pre-flight verification result."""

    executable: bool
    issues: list[ValidationIssue] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# Pipeline Metrics & Error Models (telemetry layer)
# ═══════════════════════════════════════════════════════════════════════════════


class ErrorCategory(StrEnum):
    USER = "user_error"
    SYSTEM = "system_error"
    FATAL = "fatal_error"


class ErrorCode(StrEnum):
    AMBIGUOUS_QUERY = "AMBIGUOUS_QUERY"
    NO_AGENTS_FOUND = "NO_AGENTS_FOUND"
    AGENT_UNAVAILABLE = "AGENT_UNAVAILABLE"
    MANIFEST_LINT_FAILURE = "MANIFEST_LINT_FAILURE"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_RATE_LIMIT = "LLM_RATE_LIMIT"
    VECTOR_DB_CONNECTION = "VECTOR_DB_CONNECTION"
    REGISTRY_UNAVAILABLE = "REGISTRY_UNAVAILABLE"
    INVALID_DECOMPOSITION = "INVALID_DECOMPOSITION"
    INFINITE_RECURSION = "INFINITE_RECURSION"


@dataclass
class PlanningError:
    """Structured error from the planning pipeline."""

    code: ErrorCode
    category: ErrorCategory
    message: str
    is_retriable: bool = False
    recovery_guidance: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineMetrics:
    """Telemetry for a complete pipeline run."""

    request_id: str = ""
    user_id: str = ""
    query: str = ""
    total_latency_ms: float = 0.0
    decomposition_latency_ms: float = 0.0
    resolution_latency_ms: float = 0.0
    validation_latency_ms: float = 0.0
    verification_latency_ms: float = 0.0
    llm_calls: int = 0
    llm_cost_usd: float = 0.0
    cache_hits: int = 0
    task_count: int = 0
    agent_count: int = 0
    node_count: int = 0
    edge_count: int = 0
    success: bool = False
