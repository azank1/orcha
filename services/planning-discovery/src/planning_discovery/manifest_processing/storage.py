"""Embedding storage — upserts agent embeddings via raw asyncpg SQL.

Prisma does not support pgvector operations, so we use asyncpg directly
to store and update embeddings in the ``agent_embeddings`` table.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..db.pool import AsyncpgPool

logger = logging.getLogger(__name__)

_UPSERT_SQL = """
INSERT INTO agent_embeddings (
    id, agent_id, templated_string,
    embedding, name_embedding, description_embedding,
    capabilities_embedding, tags_embedding,
    created_at, updated_at
)
VALUES (
    gen_random_uuid(), $1, $2,
    $3::vector, $4::vector, $5::vector,
    $6::vector, $7::vector,
    NOW(), NOW()
)
ON CONFLICT (agent_id)
DO UPDATE SET
    templated_string      = EXCLUDED.templated_string,
    embedding             = EXCLUDED.embedding,
    name_embedding        = EXCLUDED.name_embedding,
    description_embedding = EXCLUDED.description_embedding,
    capabilities_embedding = EXCLUDED.capabilities_embedding,
    tags_embedding        = EXCLUDED.tags_embedding,
    updated_at            = NOW()
"""


def _vec(embedding: list[float]) -> str:
    """Serialize a float list to the pgvector string format ``[f1,f2,...]``."""
    return "[" + ",".join(str(v) for v in embedding) + "]"


class EmbeddingStorage:
    """Stores and updates TDWA embeddings for agents in PostgreSQL."""

    def __init__(self, pool: AsyncpgPool) -> None:
        self._pool = pool

    async def upsert(
        self,
        agent_id: str,
        semantic_string: str,
        embeddings: dict[str, Any],
    ) -> None:
        """
        Insert or update the embedding record for *agent_id*.

        Args:
            agent_id:        The agent's DID (primary key in ``agents`` table).
            semantic_string: The TDWA templated string that was embedded.
            embeddings:      Dict returned by ``TDWAEmbeddingGenerator.generate()``.
                             Must contain keys: ``combined``, ``name``,
                             ``description``, ``capability_names``, ``tags``.
        """
        await self._pool.execute(
            _UPSERT_SQL,
            agent_id,
            semantic_string,
            _vec(embeddings["combined"]),
            _vec(embeddings["name"]),
            _vec(embeddings["description"]),
            _vec(embeddings["capability_names"]),
            _vec(embeddings["tags"]),
        )
        logger.debug("Upserted embedding for agent %s", agent_id)
