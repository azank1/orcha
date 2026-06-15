"""PnD request/response models shared between PnDClient and orchestrator node."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field

_INVALID_FUNC_CHAR_RE = re.compile(r"[^a-zA-Z0-9_-]")


def _sanitise(agent_id: str) -> str:
    return _INVALID_FUNC_CHAR_RE.sub("_", agent_id)


def candidates_to_openai_tool_schemas(
    candidates: list["ToolCandidate"],
) -> list[dict[str, Any]]:
    """Convert a list of ToolCandidate objects to OpenAI function-calling tool schemas."""
    tools: list[dict[str, Any]] = []
    for c in candidates:
        safe_id = _sanitise(c.agent_id)
        if c.protocol_type == "MCP":
            for cap in c.capabilities:
                if cap.capability_type != "TOOL":
                    continue
                tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": f"{safe_id}__{cap.capability_id}",
                            "description": f"[{c.agent_name}] {cap.description}",
                            "parameters": cap.input_schema
                            or {"type": "object", "properties": {}},
                        },
                    }
                )
        else:
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": f"delegate__{safe_id}",
                        "description": (
                            f"Delegate task to {c.agent_name}: {c.agent_description}"
                        ),
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "task": {
                                    "type": "string",
                                    "description": "Natural-language task description",
                                }
                            },
                            "required": ["task"],
                        },
                    },
                }
            )
    return tools


class CandidateCapability(BaseModel):
    capability_id: str
    capability_type: str  # "TOOL" | "RESOURCE" | "PROMPT"
    name: str
    description: str
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None


class ToolCandidate(BaseModel):
    agent_id: str
    agent_name: str
    agent_description: str
    protocol_type: str  # "MCP" | "A2A"
    relevance_score: float
    capabilities: list[CandidateCapability]
    health_status: str = "HEALTHY"


class PnDCandidateRequest(BaseModel):
    query: str
    conversation_context: list[str] = Field(default_factory=list)
    user_id: str
    top_k: int = 8
    protocol_filter: str | None = None
    exclude_agent_ids: list[str] = Field(default_factory=list)


class PnDCandidateResponse(BaseModel):
    candidates: list[ToolCandidate]
    retrieval_latency_ms: int

    def to_openai_tool_schemas(self) -> list[dict[str, Any]]:
        """Convert candidates to OpenAI function-calling tool schemas."""
        return candidates_to_openai_tool_schemas(self.candidates)
