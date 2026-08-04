"""TDWA semantic template generator.

Transforms agent manifests into TDWA-optimised semantic strings for embedding.

TDWA (Tool Document Weighted Average) format emphasises:
  - Agent name and description  (highest weight)
  - Capability names            (high weight)
  - Tags and metadata           (medium weight)
  - Detailed capability descs   (lower weight)
"""

from __future__ import annotations

import logging
from typing import Any

from .normalizer import NormalizedCapability, NormalizedManifest, normalize_manifest

logger = logging.getLogger(__name__)


class SemanticTemplateGenerator:
    """
    Generates TDWA-optimised semantic strings from agent manifests.

    Template structure::

        Agent: {name}.
        Role: {description}.
        Expertise: {tags_joined}.
        Protocol: {protocol_type}.
        Integrated Skills: {for each capability: {type} named {name} used for {description} with inputs {input_params}}.
        Networks: {supported_networks}.
        Reliability: {success_rate}%.
    """

    def generate(self, raw: dict[str, Any]) -> str:
        """Generate a semantic string from a raw agent manifest dict.

        Accepts both the nested emerge.yaml format and the flat Kafka payload
        format — ``normalize_manifest`` handles the conversion.
        """
        manifest: NormalizedManifest = normalize_manifest(raw)

        tags = ", ".join(manifest.tags)
        skills = self._format_capabilities(manifest.capabilities)
        networks = self._extract_networks(manifest.capabilities)
        networks_str = ", ".join(networks) if networks else "Not specified"

        reliability = self._calculate_reliability(raw)
        reliability_str = (
            f"{reliability:.1f}%" if reliability is not None else "Not tracked"
        )

        return (
            f"Agent: {manifest.name}. "
            f"Role: {manifest.description}. "
            f"Expertise: {tags}. "
            f"Protocol: {manifest.protocol_type}. "
            f"Integrated Skills: {skills}. "
            f"Networks: {networks_str}. "
            f"Reliability: {reliability_str}."
        )

    def _format_capabilities(self, capabilities: list[NormalizedCapability]) -> str:
        formatted = []
        for cap in capabilities:
            properties = cap.input_schema.get("properties", {})
            input_params = ", ".join(properties.keys()) if properties else "none"
            formatted.append(
                f"{cap.type.upper()} named {cap.name} used for {cap.description}"
                f" with inputs {input_params}"
            )
        return "; ".join(formatted) if formatted else "none"

    def _extract_networks(self, capabilities: list[NormalizedCapability]) -> list[str]:
        networks: set[str] = set()
        for cap in capabilities:
            properties = cap.input_schema.get("properties", {})
            if "network" in properties:
                networks.update(properties["network"].get("enum", []))
            if "chain" in properties:
                networks.update(properties["chain"].get("enum", []))
        return sorted(networks)

    def _calculate_reliability(self, raw: dict[str, Any]) -> float | None:
        # Placeholder — would be derived from PlanExecution history
        return None
