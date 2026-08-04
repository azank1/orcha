"""Unit tests for system tool registry dispatch."""

from __future__ import annotations

import pytest
from superagent.graph.state import default_state
from superagent.system_tools.registry import SystemToolRegistry, SystemToolSpec


@pytest.fixture
def registry():
    reg = SystemToolRegistry()

    async def echo_handler(args, state):
        return {"echo": args.get("message", "")}

    reg.register(
        SystemToolSpec(
            name="echo",
            description="Echo a message",
            parameters={
                "type": "object",
                "properties": {"message": {"type": "string"}},
            },
            handler=echo_handler,
        )
    )
    return reg


@pytest.mark.asyncio
async def test_dispatch_known_tool(registry):
    state = default_state("s1", "u1")
    result = await registry.call("echo", {"message": "hello"}, state)
    assert result["echo"] == "hello"


@pytest.mark.asyncio
async def test_dispatch_unknown_tool_raises(registry):
    with pytest.raises(KeyError, match="unknown_tool"):
        await registry.call("unknown_tool", {}, {})


def test_has_returns_true_for_registered(registry):
    assert registry.has("echo") is True


def test_has_returns_false_for_missing(registry):
    assert registry.has("nonexistent") is False


def test_get_all_schemas_format(registry):
    schemas = registry.get_all_schemas()
    assert len(schemas) == 1
    s = schemas[0]
    assert s["type"] == "function"
    assert s["function"]["name"] == "echo"
    assert "description" in s["function"]
    assert "parameters" in s["function"]
