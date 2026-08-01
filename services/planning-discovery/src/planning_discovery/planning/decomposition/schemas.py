"""Pydantic schemas for Stage 1 decomposition output."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class TaskDAGSchema(BaseModel):
    """JSON schema for the structured LLM output from Stage 1."""

    tasks: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    metadata: dict[str, Any] = Field(default_factory=dict)


class DecompositionResult(BaseModel):
    """Full result of the decomposition stage."""

    success: bool
    tasks: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    metadata: dict[str, Any] = Field(default_factory=dict)
    confidence: float
    method: Literal["skip", "single_pass_7b", "fallback_gpt4"]
    llm_calls: int
