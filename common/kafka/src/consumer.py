"""Abstract base Kafka consumer for Orcha services."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from aiokafka import AIOKafkaConsumer
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class KafkaConsumerConfig(BaseModel):
    """Configuration for a Kafka consumer."""

    bootstrap_servers: str
    group_id: str
    topics: list[str]
    auto_offset_reset: str = "earliest"
    enable_auto_commit: bool = True
    max_poll_records: int = 50
    session_timeout_ms: int = 30000
    heartbeat_interval_ms: int = 10000


class BaseKafkaConsumer(ABC):
    """
    Abstract base class for Kafka consumers.

    Subclasses implement ``handle_message`` to process individual messages.
    The consumer loop is resilient: per-message errors are logged and skipped
    so that a single bad message never crashes the consumer.

    Lifecycle::

        consumer = MyConsumer(config)
        await consumer.start()
        # runs in background ...
        await consumer.stop()
    """

    def __init__(self, config: KafkaConsumerConfig) -> None:
        self._config = config
        self._consumer: AIOKafkaConsumer | None = None
        self._running = False
        self._task: asyncio.Task[None] | None = None

    @abstractmethod
    async def handle_message(self, message: dict[str, Any]) -> None:
        """
        Process a single deserialized Kafka message.

        Implementations must not raise unless the error is truly unrecoverable.
        The base class will catch any exception and log it without stopping
        the consumer loop.
        """

    async def start(self) -> None:
        """Start the consumer and begin processing messages in the background."""
        if self._running:
            logger.warning("Consumer already running, ignoring start()")
            return

        self._consumer = AIOKafkaConsumer(
            *self._config.topics,
            bootstrap_servers=self._config.bootstrap_servers,
            group_id=self._config.group_id,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset=self._config.auto_offset_reset,
            enable_auto_commit=self._config.enable_auto_commit,
            max_poll_records=self._config.max_poll_records,
            session_timeout_ms=self._config.session_timeout_ms,
            heartbeat_interval_ms=self._config.heartbeat_interval_ms,
        )

        await self._consumer.start()
        self._running = True
        self._task = asyncio.create_task(
            self._consume_loop(), name=f"kafka-consumer-{self._config.group_id}"
        )
        logger.info(
            "Kafka consumer started",
            extra={
                "group_id": self._config.group_id,
                "topics": self._config.topics,
                "bootstrap_servers": self._config.bootstrap_servers,
            },
        )

    async def stop(self) -> None:
        """Gracefully stop the consumer."""
        self._running = False

        if self._task and not self._task.done():
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

        if self._consumer:
            await self._consumer.stop()
            self._consumer = None

        logger.info("Kafka consumer stopped", extra={"group_id": self._config.group_id})

    async def _consume_loop(self) -> None:
        """Internal message consumption loop."""
        assert self._consumer is not None  # noqa: S101 — guaranteed by start()

        try:
            async for message in self._consumer:
                if not self._running:
                    break
                try:
                    await self.handle_message(message.value)
                except Exception:
                    logger.exception(
                        "Failed to process Kafka message — skipping",
                        extra={
                            "topic": message.topic,
                            "partition": message.partition,
                            "offset": message.offset,
                        },
                    )
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Kafka consumer loop encountered a fatal error")
            raise
