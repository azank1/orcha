"""ContextWindowManager — pagination and compression when approaching token budget."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import BaseMessage, SystemMessage

from ..config import settings

logger = logging.getLogger(__name__)

_CHARS_PER_TOKEN = 4  # rough approximation


def _count_tokens(messages: list[BaseMessage]) -> int:
    total = sum(len(str(getattr(m, "content", ""))) for m in messages)
    return total // _CHARS_PER_TOKEN


class ContextWindowManager:
    """Manages context window size to stay within token budget."""

    @staticmethod
    def maybe_compress(state: dict[str, Any]) -> list[BaseMessage] | None:
        """
        If estimated token usage exceeds the compression threshold, compress
        older messages.  Returns a replacement messages list or None if no
        compression was needed.
        """
        messages: list[BaseMessage] = state.get("messages", [])
        token_count = _count_tokens(messages)
        budget = settings.token_budget
        threshold = settings.compression_threshold
        keep_last = settings.keep_last_messages

        if token_count < budget * threshold:
            return None

        logger.info(
            "Context compression triggered: ~%d tokens (%.0f%% of %d budget)",
            token_count,
            100 * token_count / budget,
            budget,
        )

        # Keep the last N messages intact
        recent = messages[-keep_last:]
        older = messages[:-keep_last]

        if not older:
            return None  # Can't compress — everything is recent

        # Summarise older messages into a single system message
        summary_text = ContextWindowManager._summarise(older)
        summary_msg = SystemMessage(
            content=f"[Conversation summary — {len(older)} earlier messages compressed]\n\n{summary_text}"
        )

        compressed = [summary_msg] + recent
        logger.info(
            "Compressed %d messages → 1 summary + %d recent = %d total",
            len(older),
            len(recent),
            len(compressed),
        )
        return compressed

    @staticmethod
    def _summarise(messages: list[BaseMessage]) -> str:
        """Produce a plain-text summary of older messages without an LLM call."""
        parts: list[str] = []
        for msg in messages:
            role = type(msg).__name__.replace("Message", "").lower()
            content = str(getattr(msg, "content", ""))
            if content:
                parts.append(f"{role}: {content[:200]}")
        return "\n".join(parts)
