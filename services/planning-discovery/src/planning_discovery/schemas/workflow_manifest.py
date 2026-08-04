"""Workflow manifest schema — the final output of the planning pipeline."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class NodeType(StrEnum):
    """Types of nodes in a workflow DAG."""

    STANDARD = "standard"  # Concrete agent invocation
    ROUTER = "router"  # Conditional branching
    SYSTEM_TOOL = "system_tool"  # Built-in utility (sleep, approval, loop_control)


class CapabilityReference(BaseModel):
    """Reference to the exact agent capability selected for a node."""

    capability_id: str  # e.g. "search_flights"
    type: str  # TOOL | RESOURCE | PROMPT
    name: str
    input_schema: dict[str, Any] = Field(
        default_factory=dict
    )  # Full schema from manifest
    output_schema: dict[str, Any] = Field(
        default_factory=dict
    )  # Full schema from manifest


class TaskDescriptor(BaseModel):
    """Task context with resolved inputs for a standard node."""

    description: str
    # Can contain literal values OR $tasks.<id>.output.<field> data references
    inputs: dict[str, Any] = Field(default_factory=dict)
    unresolved_inputs: list[str] = Field(
        default_factory=list
    )  # Fields needing human input


class HumanInputNode(BaseModel):
    """Human-in-the-loop node that collects missing required inputs before execution."""

    id: str = "hitl_input_collection"
    type: str = NodeType.SYSTEM_TOOL
    tool: str = "human_input"
    # inputs.requests: list of {target_task, field_name, prompt, ...}
    inputs: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    outputs: dict[str, Any] = Field(default_factory=lambda: {"collected_inputs": {}})


class StandardNode(BaseModel):
    """Node representing a concrete agent invocation."""

    id: str
    type: str = NodeType.STANDARD
    agent_id: str  # DID of the resolved agent
    description: str = ""
    dependencies: list[str] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)
    orchestration_hint: str | None = None  # e.g. "recursive_subgraph"
    # IO-resolved fields (populated after Stage 2b)
    capability: CapabilityReference | None = None  # Exact capability from manifest
    task: TaskDescriptor | None = None  # Task descriptor with resolved inputs
    unresolved_inputs: list[str] = Field(default_factory=list)
    field_mappings: list[dict[str, Any]] = Field(default_factory=list)


class RouterNode(BaseModel):
    """Node representing conditional branching logic."""

    id: str
    type: str = NodeType.ROUTER
    routing_key: str
    branches: list[dict[str, Any]] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)


class SystemToolNode(BaseModel):
    """Node for built-in system utilities."""

    id: str
    type: str = NodeType.SYSTEM_TOOL
    tool_name: str
    inputs: dict[str, Any] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)


class Edge(BaseModel):
    """Directed edge in the workflow DAG."""

    source: str
    target: str
    condition: str | None = None


class WorkflowManifest(BaseModel):
    """
    Complete workflow specification produced by the planning pipeline.

    This is the final output returned to callers of ``POST /api/v1/plan``.
    """

    id: str
    version: str = "1.0"
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    # Graph structure
    nodes: list[dict[str, Any]]  # Flexible — parsed as typed nodes by execution engine
    edges: list[dict[str, Any]]
    entry_node_id: str

    # Planning metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Validation metadata
    validated: bool = False
    validation_tier: str = "deterministic"
    confidence_score: float = 0.0
