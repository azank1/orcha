"""Kafka producer for Metaorcha services."""

from __future__ import annotations

import json
import logging
from typing import Any

from aiokafka import AIOKafkaProducer
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class KafkaProducerConfig(BaseModel):
    """Configuration for a Kafka producer."""

    bootstrap_servers: str
    max_request_size: int = 1048576  # 1 MB
    request_timeout_ms: int = 30000
    retry_backoff_ms: int = 1000


class KafkaProducer:
    """
    Async Kafka producer.

    Usage::

        producer = KafkaProducer(config)
        await producer.start()
        await producer.publish("my.topic", payload={"key": "value"})
        await producer.stop()
    """

    def __init__(self, config: KafkaProducerConfig) -> None:
        self._config = config
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        """Start the underlying AIOKafkaProducer."""
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._config.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            max_request_size=self._config.max_request_size,
            request_timeout_ms=self._config.request_timeout_ms,
            retry_backoff_ms=self._config.retry_backoff_ms,
        )
        await self._producer.start()
        logger.info(
            "Kafka producer started",
            extra={"bootstrap_servers": self._config.bootstrap_servers},
        )

    async def stop(self) -> None:
        """Flush pending messages and stop the producer."""
        if self._producer:
            await self._producer.stop()
            self._producer = None
            logger.info("Kafka producer stopped")

    async def publish(
        self,
        topic: str,
        payload: dict[str, Any],
        key: str | None = None,
    ) -> None:
        """
        Publish a JSON-serializable payload to a Kafka topic.

        Args:
            topic:   Target Kafka topic name.
            payload: Dict that will be JSON-serialized as the message value.
            key:     Optional message key (string, encoded as UTF-8).

        Raises:
            RuntimeError: If the producer has not been started.
        """
        if self._producer is None:
            raise RuntimeError(
                "KafkaProducer has not been started — call start() first"
            )

        encoded_key = key.encode("utf-8") if key else None
        await self._producer.send_and_wait(topic, value=payload, key=encoded_key)
        logger.debug("Published Kafka message", extra={"topic": topic, "key": key})
