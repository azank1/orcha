"""PlaywrightBackend — real computer-use backend driving headless Chromium.

Selected with COMPUTER_USE_BACKEND=playwright (the mock stays the default).
A driver model (COMPUTER_USE_MODEL, via the superagent's OpenAI-compatible
client settings) observes each page — screenshot + truncated DOM text — and
replies with the next action as strict JSON. Every step's screenshot is
persisted via the artifact store and emitted as an artifact_created event, so
the run's Artifacts panel renders a flipbook of the browsing session.

Sandbox safety: navigation is restricted to COMPUTER_USE_ALLOWED_DOMAINS
(comma-separated, default en.wikipedia.org,example.com); localhost and
private hosts are never allowed. Any Playwright/LLM failure becomes an
"Error: computer-use failed: ..." result string — nothing raises into the graph.
"""

from __future__ import annotations

import asyncio
import base64
import ipaddress
import json
import logging
import os
import re
import time
from typing import Any
from urllib.parse import urlparse

from langchain_core.callbacks.manager import adispatch_custom_event
from langchain_core.runnables import RunnableConfig
from openai import AsyncOpenAI

from ..artifact_store import persist_agent_output_bytes
from ..config import settings
from .computer_use_handler import ComputerUseBackend

try:  # Playwright is optional at import time — the mock backend needs nothing.
    from playwright.async_api import async_playwright
except ImportError:  # pragma: no cover - depends on install environment
    async_playwright = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

_MAX_STEPS = 8
_STEP_TIMEOUT_S = 15
_DOM_SNAPSHOT_CHARS = 1500
_DEFAULT_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
_DEFAULT_ALLOWED_DOMAINS = "en.wikipedia.org,example.com"

_SYSTEM_PROMPT = """\
You are a web-browsing driver. You are given a goal, the current page URL, a
truncated text snapshot of the page, and a screenshot. Reply with EXACTLY one
JSON object (no prose, no markdown fences) choosing the next action:

{"action": "goto", "target": "<url>"}                       — navigate
{"action": "click", "target": "<css selector or text=...>"} — click an element
{"action": "type", "target": "<css selector>", "text": "<text to type>"}
{"action": "done", "text": "<one-line summary of the outcome>"}

Only navigate to these allowed domains: __DOMAINS__.
Pick "done" as soon as the goal is satisfied or cannot be progressed."""


class _DomainBlocked(Exception):
    """goto target rejected by the domain allowlist."""


def _allowed_domains() -> list[str]:
    raw = os.getenv("COMPUTER_USE_ALLOWED_DOMAINS", _DEFAULT_ALLOWED_DOMAINS)
    return [d.strip().lower() for d in raw.split(",") if d.strip()]


def _is_private_host(host: str) -> bool:
    if host == "localhost" or host.endswith((".local", ".internal")):
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
    )


def check_url_allowed(url: str, allowed: list[str]) -> str | None:
    """Return None if url may be visited, else a human-readable rejection."""
    parsed = urlparse(url if "://" in url else f"https://{url}")
    host = (parsed.hostname or "").lower()
    if not host:
        return f"unparseable URL {url!r}"
    if _is_private_host(host):
        return f"host {host!r} is localhost/private"
    if not any(host == d or host.endswith(f".{d}") for d in allowed):
        return f"domain {host!r} not in COMPUTER_USE_ALLOWED_DOMAINS"
    return None


def parse_action_json(text: str) -> dict[str, Any]:
    """Parse the driver model's reply as an action dict.

    Tolerates markdown-fenced output (```json ... ```) and prose around the
    JSON object. Raises ValueError on anything unparseable or on an unknown
    action verb.
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\s*\n?", "", cleaned)
        cleaned = re.sub(r"\n?\s*```$", "", cleaned.strip())
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end <= start:
        raise ValueError(f"no JSON object in model reply: {text[:120]!r}")
    data = json.loads(cleaned[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError(f"model reply is not a JSON object: {text[:120]!r}")
    action = str(data.get("action", "")).strip().lower()
    if action not in ("goto", "click", "type", "done"):
        raise ValueError(f"unknown action {action!r}")
    return {
        "action": action,
        "target": data.get("target"),
        "text": data.get("text"),
    }


def _build_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )


def _looks_like_url(value: str) -> bool:
    return "://" in value or "." in value.split("/")[0]


class PlaywrightBackend(ComputerUseBackend):
    """Drives headless Chromium via Playwright; a vision model picks each action.

    Context keys the handler injects into ``extra`` (underscore-prefixed):
    ``_session_id`` / ``_user_id`` scope artifact persistence, ``_config``
    carries the LangGraph config for artifact_created stream events.
    """

    def __init__(self) -> None:
        self._model = os.getenv("COMPUTER_USE_MODEL", _DEFAULT_MODEL).strip()
        self._allowed = _allowed_domains()

    async def execute_action(
        self,
        action: str,
        target: str | None,
        extra: dict[str, Any],
    ) -> dict[str, Any]:
        goal = str(extra.get("task") or extra.get("goal") or "").strip()
        if not goal:
            goal = " ".join(p for p in (action, str(target or "")) if p).strip()
        session_id = str(extra.get("_session_id") or "")
        user_id = str(extra.get("_user_id") or "")
        config = extra.get("_config")

        # Total budget: stay comfortably under the pipeline's per-agent-call
        # ceiling (agent_call_timeout_seconds, default 60s).
        budget = max(20.0, float(settings.agent_call_timeout_seconds or 60) - 15.0)
        steps: list[str] = []
        shots: list[str] = []
        try:
            await asyncio.wait_for(
                self._drive(
                    goal=goal,
                    seed_target=str(target) if target else None,
                    session_id=session_id,
                    user_id=user_id,
                    config=config,
                    steps=steps,
                    shots=shots,
                    deadline=time.monotonic() + budget,
                ),
                timeout=budget,
            )
        except _DomainBlocked as exc:
            return {
                "success": False,
                "result": f"Error: computer-use blocked: {exc}",
                "backend": "playwright",
            }
        except TimeoutError:
            steps.append("stopped: time budget exhausted")
        except Exception as exc:  # never raise into the graph
            logger.exception("PlaywrightBackend failed")
            return {
                "success": False,
                "result": f"Error: computer-use failed: {exc}",
                "backend": "playwright",
            }
        summary = ", ".join(steps) if steps else "no actions taken"
        return {
            "success": True,
            "result": (
                f"computer-use ({goal[:80]}): {summary} — "
                f"{len(steps)} steps, {len(shots)} screenshots in artifacts"
            ),
            "backend": "playwright",
        }

    # ------------------------------------------------------------------
    # Driver loop
    # ------------------------------------------------------------------

    async def _drive(
        self,
        *,
        goal: str,
        seed_target: str | None,
        session_id: str,
        user_id: str,
        config: RunnableConfig | None,
        steps: list[str],
        shots: list[str],
        deadline: float,
    ) -> None:
        if async_playwright is None:
            raise RuntimeError("playwright package is not installed")
        client = _build_client()
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
            try:
                page = await browser.new_page(viewport={"width": 1280, "height": 800})
                if seed_target and _looks_like_url(seed_target):
                    self._check_allowed(seed_target)
                    await asyncio.wait_for(
                        page.goto(seed_target, wait_until="domcontentloaded"),
                        timeout=_STEP_TIMEOUT_S,
                    )
                    steps.append(f"visited {seed_target}")
                for step in range(1, _MAX_STEPS + 1):
                    if time.monotonic() > deadline:
                        steps.append("stopped: time budget exhausted")
                        break
                    try:
                        decision = await asyncio.wait_for(
                            self._observe_and_decide(
                                client,
                                page,
                                goal,
                                steps,
                                shots,
                                session_id,
                                user_id,
                                config,
                            ),
                            timeout=_STEP_TIMEOUT_S,
                        )
                    except TimeoutError:
                        steps.append(f"step {step}: timed out (>15s)")
                        break
                    except ValueError as exc:
                        steps.append(f"stopped: {exc}")
                        break
                    if decision is None:  # model said "done"
                        break
                    await self._apply(decision, page, steps)
            finally:
                await browser.close()

    async def _observe_and_decide(
        self,
        client: AsyncOpenAI,
        page: Any,
        goal: str,
        steps: list[str],
        shots: list[str],
        session_id: str,
        user_id: str,
        config: RunnableConfig | None,
    ) -> dict[str, Any] | None:
        """Screenshot the page, persist the flipbook frame, ask for the next action.

        Returns the parsed action dict, or None when the model says "done".
        """
        png: bytes = await page.screenshot()
        dom: str = await page.evaluate(
            f"() => document.body ? document.body.innerText.slice(0, {_DOM_SNAPSHOT_CHARS}) : ''"
        )
        url = str(page.url)
        await self._persist_shot(
            png, len(shots) + 1, url, shots, session_id, user_id, config
        )
        history = "; ".join(steps[-4:]) or "none"
        resp = await client.chat.completions.create(
            model=self._model,
            max_tokens=300,
            messages=[
                {
                    "role": "system",
                    "content": _SYSTEM_PROMPT.replace(
                        "__DOMAINS__", ", ".join(self._allowed)
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"Goal: {goal}\nCurrent URL: {url}\n"
                                f"Recent steps: {history}\n"
                                f"Page text (truncated):\n{dom}"
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "data:image/png;base64,"
                                + base64.b64encode(png).decode()
                            },
                        },
                    ],
                },
            ],
        )
        decision = parse_action_json(resp.choices[0].message.content or "")
        if decision["action"] == "done":
            if decision.get("text"):
                steps.append(str(decision["text"]))
            return None
        return decision

    async def _apply(
        self, decision: dict[str, Any], page: Any, steps: list[str]
    ) -> None:
        act = decision["action"]
        target = str(decision.get("target") or "")
        try:
            if act == "goto":
                self._check_allowed(target)
                await asyncio.wait_for(
                    page.goto(target, wait_until="domcontentloaded"),
                    timeout=_STEP_TIMEOUT_S,
                )
                steps.append(f"visited {target}")
            elif act == "click":
                await asyncio.wait_for(page.click(target), timeout=_STEP_TIMEOUT_S)
                steps.append(f"clicked {target}")
            elif act == "type":
                text = str(decision.get("text") or "")
                await asyncio.wait_for(page.fill(target, text), timeout=_STEP_TIMEOUT_S)
                steps.append(f"typed into {target}")
        except _DomainBlocked:
            raise
        except Exception as exc:
            steps.append(f"{act} {target} failed: {exc}")

    def _check_allowed(self, url: str) -> None:
        reason = check_url_allowed(url, self._allowed)
        if reason:
            raise _DomainBlocked(reason)

    async def _persist_shot(
        self,
        png: bytes,
        step: int,
        url: str,
        shots: list[str],
        session_id: str,
        user_id: str,
        config: RunnableConfig | None,
    ) -> None:
        """Best-effort: a failed upload never kills the browsing loop."""
        filename = f"computer-use-step-{step}.png"
        try:
            result = await persist_agent_output_bytes(
                png, "image/png", filename, session_id, user_id
            )
            ref = result.get("artifact")
            shots.append(filename)
            logger.info("computer-use step %d screenshot stored (%s)", step, url)
            if ref is not None and config:
                await adispatch_custom_event(
                    "agent_invocation",
                    {
                        "type": "artifact_created",
                        "artifact_id": getattr(ref, "artifact_id", ""),
                        "filename": getattr(ref, "filename", filename),
                        "mime_type": getattr(ref, "mime_type", "image/png"),
                        "size_bytes": getattr(ref, "size_bytes", len(png)),
                        "source": "AGENT_OUTPUT",
                    },
                    config=config,
                )
        except Exception:
            logger.warning("computer-use screenshot persist failed", exc_info=True)
