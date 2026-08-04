"""Agent manifest normalizer.

Converts any supported raw manifest format into a single ``NormalizedManifest``
that the rest of the manifest-processing pipeline consumes.

Supported input formats
-----------------------
1. **emerge.yaml / fixture format** (nested):
   ``identity.name``, ``protocol.type``,
   ``capabilities: {tools: [...], resources: [...], prompts: [...], skills: [...]}``

2. **Kafka payload format** (flat, emitted by the registry after harvesting):
   top-level ``name``, ``protocol_type``,
   ``capabilities: [{name, description, type, input_schema, output_schema}, ...]``
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class NormalizedCapability(BaseModel):
    name: str
    description: str
    type: str = "tool"  # "tool" | "resource" | "prompt"
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)


class NormalizedManifest(BaseModel):
    name: str
    description: str
    tags: list[str] = Field(default_factory=list)
    protocol_type: str  # uppercase: "MCP" | "A2A"
    capabilities: list[NormalizedCapability] = Field(default_factory=list)


def normalize_manifest(raw: dict[str, Any]) -> NormalizedManifest:
    """
    Return a ``NormalizedManifest`` from *raw*, regardless of its original format.

    The normalizer is the single source-of-truth for field extraction — both
    generators delegate to this function so that format-specific logic lives
    in one place.
    """
    # ── Identity ──────────────────────────────────────────────────────────────
    identity = raw.get("identity") or {}
    name = identity.get("name") or raw.get("name") or "Unknown Agent"
    description = identity.get("description") or raw.get("description") or ""
    tags: list[str] = identity.get("tags") or raw.get("tags") or []

    # ── Protocol ──────────────────────────────────────────────────────────────
    protocol = raw.get("protocol") or {}
    protocol_type = (
        protocol.get("type") or raw.get("protocol_type") or "unknown"
    ).upper()

    # ── Capabilities ──────────────────────────────────────────────────────────
    raw_caps = raw.get("capabilities") or []
    capabilities: list[NormalizedCapability] = []

    if isinstance(raw_caps, list):
        # ── Kafka payload format: flat list ───────────────────────────────────
        for cap in raw_caps:
            capabilities.append(
                NormalizedCapability(
                    name=cap.get("name") or "",
                    description=cap.get("description") or "",
                    type=(cap.get("type") or "tool").lower(),
                    input_schema=cap.get("input_schema") or {},
                    output_schema=cap.get("output_schema") or {},
                )
            )

    elif isinstance(raw_caps, dict):
        # ── emerge.yaml / fixture format: sub-keyed dict ──────────────────────
        for tool in raw_caps.get("tools") or []:
            capabilities.append(
                NormalizedCapability(
                    name=tool.get("name") or "",
                    description=tool.get("description") or "",
                    type="tool",
                    # MCP tools use camelCase keys in the YAML spec
                    input_schema=tool.get("inputSchema")
                    or tool.get("input_schema")
                    or {},
                    output_schema=tool.get("outputSchema")
                    or tool.get("output_schema")
                    or {},
                )
            )
        for resource in raw_caps.get("resources") or []:
            capabilities.append(
                NormalizedCapability(
                    name=resource.get("name") or "",
                    description=resource.get("description") or "",
                    type="resource",
                )
            )
        for prompt in raw_caps.get("prompts") or []:
            capabilities.append(
                NormalizedCapability(
                    name=prompt.get("name") or "",
                    description=prompt.get("description") or "",
                    type="prompt",
                )
            )
        # A2A skills — map to "tool" in the normalized form
        for skill in raw_caps.get("skills") or []:
            capabilities.append(
                NormalizedCapability(
                    name=skill.get("name") or "",
                    description=skill.get("description") or "",
                    type="tool",
                    input_schema=skill.get("input_schema") or {},
                    output_schema=skill.get("output_schema") or {},
                )
            )

    return NormalizedManifest(
        name=name,
        description=description,
        tags=tags,
        protocol_type=protocol_type,
        capabilities=capabilities,
    )
