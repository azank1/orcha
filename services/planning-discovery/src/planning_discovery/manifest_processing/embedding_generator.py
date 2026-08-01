"""TDWA embedding generator.

Generates 1536-dimensional TDWA (Tool Document Weighted Average) embeddings
for agent manifests via the configured LLM provider.

TDWA weights (from ScaleMCP research):
  name              0.30
  description       0.25
  capability_names  0.20
  tags              0.15
  capability_descs  0.10
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import numpy as np

from .normalizer import NormalizedManifest, normalize_manifest

if TYPE_CHECKING:
    from common.llm.src import LLMProvider

logger = logging.getLogger(__name__)

TDWA_WEIGHTS: dict[str, float] = {
    "name": 0.30,
    "description": 0.25,
    "capability_names": 0.20,
    "tags": 0.15,
    "capability_descriptions": 0.10,
}

_EMBEDDING_DIM_FALLBACK = 768  # used only when every component is empty


class TDWAEmbeddingGenerator:
    """
    Generates TDWA embeddings from agent manifests.

    Each component (name, description, capability_names, tags,
    capability_descriptions) is embedded separately, then combined
    into a weighted-average ``combined`` vector.
    """

    def __init__(self, llm_provider: LLMProvider, embedding_model: str) -> None:
        self._llm = llm_provider
        self._embedding_model = embedding_model

    async def generate(self, raw: dict[str, Any]) -> dict[str, list[float]]:
        """
        Generate all TDWA component embeddings plus the combined vector.

        Accepts both the nested emerge.yaml format and the flat Kafka payload
        format — ``normalize_manifest`` handles the conversion.

        Returns:
            Dict with keys: ``combined``, ``name``, ``description``,
            ``capability_names``, ``tags``, ``capability_descriptions``.
            Each value is a list of floats of length ``EMBEDDING_DIM``.
        """
        manifest: NormalizedManifest = normalize_manifest(raw)

        components = {
            "name": manifest.name,
            "description": manifest.description,
            "capability_names": " ".join(c.name for c in manifest.capabilities),
            "tags": " ".join(manifest.tags),
            "capability_descriptions": " ".join(
                c.description for c in manifest.capabilities
            ),
        }

        # First pass: embed non-empty components so we know the actual dimension
        embeddings: dict[str, list[float]] = {}
        empty_keys: list[str] = []

        for component_name, text in components.items():
            if not text.strip():
                empty_keys.append(component_name)
            else:
                embeddings[component_name] = await self._llm.embed(
                    text, self._embedding_model
                )

        # Infer dimension from the first real embedding; fall back if all empty
        dim = (
            len(next(iter(embeddings.values())))
            if embeddings
            else _EMBEDDING_DIM_FALLBACK
        )

        # Zero-pad components that had no text, using the actual model dimension
        for key in empty_keys:
            embeddings[key] = [0.0] * dim

        # Weighted average (TDWA)
        combined = np.zeros(dim, dtype=np.float64)
        for component, weight in TDWA_WEIGHTS.items():
            combined += weight * np.array(embeddings[component], dtype=np.float64)

        embeddings["combined"] = combined.tolist()
        return embeddings
