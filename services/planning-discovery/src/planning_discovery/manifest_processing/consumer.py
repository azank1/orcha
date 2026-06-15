"""Kafka consumer for agent manifest registration events.

Listens on ``registry.agent.registered``, generates TDWA embeddings,
and stores them in PostgreSQL via the asyncpg pool.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from common.kafka.src import BaseKafkaConsumer, KafkaConsumerConfig, KafkaTopics

from .storage import EmbeddingStorage
from .template_generator import SemanticTemplateGenerator

if TYPE_CHECKING:
    from ..db.pool import AsyncpgPool
    from .embedding_generator import TDWAEmbeddingGenerator

logger = logging.getLogger(__name__)


class ManifestConsumer(BaseKafkaConsumer):
    """
    Consumes ``registry.agent.registered`` events and stores TDWA embeddings.

    Pipeline per message::

        Kafka event → SemanticTemplateGenerator → TDWAEmbeddingGenerator → EmbeddingStorage
    """

    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str,
        pool: AsyncpgPool,
        embedding_generator: TDWAEmbeddingGenerator,
    ) -> None:
        config = KafkaConsumerConfig(
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            topics=[KafkaTopics.REGISTRY_AGENT_REGISTERED],
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )
        super().__init__(config)

        self._template_gen = SemanticTemplateGenerator()
        self._embedding_gen = embedding_generator
        self._storage = EmbeddingStorage(pool)

    async def handle_message(self, message: dict[str, Any]) -> None:
        """Process a single manifest registration event."""
        agent_id: str | None = message.get("agent_id")
        manifest: dict[str, Any] | None = message.get("manifest")

        if not agent_id or not manifest:
            logger.warning(
                "Skipping malformed manifest event — missing agent_id or manifest: %s",
                message,
            )
            return

        logger.info("Processing manifest for agent %s", agent_id)

        semantic_string = self._template_gen.generate(manifest)
        embeddings = await self._embedding_gen.generate(manifest)
        await self._storage.upsert(agent_id, semantic_string, embeddings)

        logger.info("Stored embedding for agent %s", agent_id)
