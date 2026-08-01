"""PlaywrightBackend — domain allowlist, action-JSON parsing, driver loop.

Playwright and the driver model client are faked — no network, no real browser.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from superagent.handlers import computer_use_playwright as cu
from superagent.handlers.computer_use_playwright import (
    PlaywrightBackend,
    check_url_allowed,
    parse_action_json,
)

_ALLOWED = ["en.wikipedia.org", "example.com"]


# ── Domain allowlist ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        "https://en.wikipedia.org/wiki/Agent",
        "en.wikipedia.org/wiki/Agent",
        "https://www.example.com/path?q=1",
    ],
)
def test_allowlist_allows_configured_domains(url: str) -> None:
    assert check_url_allowed(url, _ALLOWED) is None


@pytest.mark.parametrize(
    "url",
    [
        "https://google.com",
        "https://en.wikipedia.org.evil.com",
        "not a url at all !!",
    ],
)
def test_allowlist_rejects_non_allowed_hosts(url: str) -> None:
    assert check_url_allowed(url, _ALLOWED) is not None


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:8080/admin",
        "http://127.0.0.1/x",
        "http://[::1]/x",
        "http://192.168.1.10/internal",
        "http://10.0.0.5/internal",
        "http://host.docker.internal/x",
    ],
)
def test_allowlist_rejects_localhost_and_private_hosts(url: str) -> None:
    # Private/loopback hosts are blocked even when present in the allowlist.
    assert check_url_allowed(url, _ALLOWED + ["localhost"]) is not None


# ── Action-JSON parsing ───────────────────────────────────────────────────────


def test_parse_action_plain_json() -> None:
    assert parse_action_json('{"action": "goto", "target": "https://x.co"}') == {
        "action": "goto",
        "target": "https://x.co",
        "text": None,
    }


def test_parse_action_tolerates_markdown_fence() -> None:
    fenced = '```json\n{"action": "type", "target": "#q", "text": "hi"}\n```'
    assert parse_action_json(fenced) == {
        "action": "type",
        "target": "#q",
        "text": "hi",
    }


def test_parse_action_tolerates_surrounding_prose() -> None:
    reply = 'The next step is: {"action": "done", "text": "all done"} — finished.'
    assert parse_action_json(reply) == {
        "action": "done",
        "target": None,
        "text": "all done",
    }


def test_parse_action_rejects_garbage_and_unknown_verbs() -> None:
    with pytest.raises(ValueError):
        parse_action_json("no json here at all")
    with pytest.raises(ValueError):
        parse_action_json('{"action": "delete_everything"}')


# ── Driver loop (faked Playwright + model client) ────────────────────────────


class _FakePage:
    def __init__(self) -> None:
        self.url = "about:blank"
        self.goto_calls: list[str] = []

    async def goto(self, url: str, wait_until: str | None = None) -> None:
        self.goto_calls.append(url)
        self.url = url

    async def screenshot(self) -> bytes:
        return b"\x89PNG-fake"

    async def evaluate(self, script: str) -> str:
        return "Example Domain page text"

    async def click(self, target: str) -> None:
        pass

    async def fill(self, target: str, text: str) -> None:
        pass


class _FakeBrowser:
    def __init__(self, page: _FakePage) -> None:
        self._page = page

    async def new_page(self, **kwargs) -> _FakePage:
        return self._page

    async def close(self) -> None:
        pass


class _FakePlaywrightCtx:
    def __init__(self, page: _FakePage) -> None:
        self._page = page

    async def __aenter__(self):
        chromium = SimpleNamespace(
            launch=AsyncMock(return_value=_FakeBrowser(self._page))
        )
        return SimpleNamespace(chromium=chromium)

    async def __aexit__(self, *args) -> None:
        pass


def _text_response(text: str):
    choice = SimpleNamespace(message=SimpleNamespace(content=text))
    return SimpleNamespace(choices=[choice])


def _fake_ref(filename: str):
    return SimpleNamespace(
        artifact_id=f"art-{filename}",
        filename=filename,
        mime_type="image/png",
        size_bytes=10,
        s3_bucket="",
        s3_key="",
    )


async def test_loop_stops_on_done_and_persists_flipbook(monkeypatch) -> None:
    page = _FakePage()
    monkeypatch.setattr(cu, "async_playwright", lambda: _FakePlaywrightCtx(page))

    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=AsyncMock(
                    side_effect=[
                        _text_response(
                            '{"action": "goto", "target": "https://example.com"}'
                        ),
                        _text_response(
                            '```json\n{"action": "done", "text": "saw the page"}\n```'
                        ),
                    ]
                )
            )
        )
    )
    monkeypatch.setattr(cu, "_build_client", lambda: client)

    persisted: list[str] = []

    async def _fake_persist(data, mime, filename, session_id, user_id):
        persisted.append(filename)
        return {"content": "ok", "artifact": _fake_ref(filename)}

    monkeypatch.setattr(cu, "persist_agent_output_bytes", _fake_persist)

    backend = PlaywrightBackend()
    result = await backend.execute_action(
        "navigate", "https://example.com", {"_session_id": "s1", "_user_id": "u1"}
    )

    assert result["success"] is True
    assert result["backend"] == "playwright"
    assert "visited https://example.com" in result["result"]
    assert "screenshots in artifacts" in result["result"]
    # Seed goto + model-driven goto; one screenshot per observe step (2).
    assert page.goto_calls == ["https://example.com", "https://example.com"]
    assert persisted == ["computer-use-step-1.png", "computer-use-step-2.png"]


async def test_loop_returns_error_string_on_blocked_domain(monkeypatch) -> None:
    page = _FakePage()
    monkeypatch.setattr(cu, "async_playwright", lambda: _FakePlaywrightCtx(page))
    monkeypatch.setattr(cu, "_build_client", lambda: SimpleNamespace())

    backend = PlaywrightBackend()
    result = await backend.execute_action(
        "navigate", "http://169.254.169.254/latest/meta-data", {}
    )

    assert result["success"] is False
    assert result["result"].startswith("Error: computer-use blocked:")


async def test_loop_returns_error_string_when_playwright_missing(monkeypatch) -> None:
    monkeypatch.setattr(cu, "async_playwright", None)

    backend = PlaywrightBackend()
    result = await backend.execute_action("screenshot", None, {})

    assert result["success"] is False
    assert result["result"].startswith("Error: computer-use failed:")
