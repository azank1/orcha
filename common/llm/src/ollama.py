"""Ollama LLM provider implementation."""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING, Any

import httpx

from .provider import LLMProvider

if TYPE_CHECKING:
    from .config import LLMConfig

logger = logging.getLogger(__name__)

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def _extract_json(text: str) -> str:
    """Return the JSON payload from *text*, stripping markdown fences if present."""
    text = text.strip()
    match = _JSON_FENCE_RE.search(text)
    if match:
        return match.group(1).strip()
    # No fences — return as-is; json.loads will surface any parse errors clearly
    return text


class OllamaProvider(LLMProvider):
    """
    LLM provider backed by a local Ollama instance.

    Communicates with Ollama's REST API (default: http://localhost:11434).
    Useful for local development and offline environments.

    Note: Ollama's embedding endpoint requires models that support embeddings
    (e.g. ``nomic-embed-text``, ``mxbai-embed-large``).
    """

    def __init__(self, config: LLMConfig) -> None:
        self._config = config
        self._client = httpx.AsyncClient(
            base_url=config.ollama_base_url,
            timeout=config.timeout,
        )

    async def complete(
        self,
        model: str,
        messages: list[dict[str, str]],
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.3,
    ) -> str:
        wants_json = response_format and response_format.get("type") in (
            "json_object",
            "json_schema",
        )

        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if wants_json:
            body["format"] = "json"

        response = await self._request_with_retry("POST", "/api/chat", json=body)
        data = response.json()

        content: str = data["message"]["content"]

        if wants_json:
            content = _extract_json(content)
            try:
                json.loads(content)  # validate it parses
            except json.JSONDecodeError as exc:
                raise ValueError(f"Ollama returned invalid JSON: {content!r}") from exc

        return content

    async def embed(self, text: str, model: str) -> list[float]:
        body = {"model": model, "prompt": text}
        response = await self._request_with_retry("POST", "/api/embeddings", json=body)
        data = response.json()
        return data["embedding"]

    async def _request_with_retry(
        self, method: str, path: str, **kwargs: Any
    ) -> httpx.Response:
        import asyncio

        last_exc: Exception | None = None
        delay = self._config.retry_delay

        for attempt in range(1, self._config.max_retries + 1):
            try:
                response = await self._client.request(method, path, **kwargs)
                response.raise_for_status()
                return response
            except (
                httpx.TimeoutException,
                httpx.ConnectError,
                httpx.HTTPStatusError,
            ) as exc:
                last_exc = exc
                if (
                    isinstance(exc, httpx.HTTPStatusError)
                    and exc.response.status_code < 500
                ):
                    raise
                logger.warning(
                    "Ollama request failed (attempt %d/%d): %s",
                    attempt,
                    self._config.max_retries,
                    exc,
                )
                if attempt < self._config.max_retries:
                    await asyncio.sleep(delay)
                    delay *= 2

        raise RuntimeError(
            f"Ollama request failed after {self._config.max_retries} attempts"
        ) from last_exc

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()
