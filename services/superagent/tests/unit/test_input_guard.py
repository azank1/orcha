"""Unit tests for InputGuard."""

import pytest
from superagent.middleware.input_guard import InputGuard, InputGuardError

_SCHEMA = {
    "type": "object",
    "properties": {
        "to": {"type": "string"},
        "subject": {"type": "string"},
        "body": {"type": "string"},
        "page": {"type": "integer"},
        "page_size": {"type": "integer"},
    },
    "required": ["to", "subject", "body"],
}


def test_valid_args_pass():
    args = {"to": "alice@example.com", "subject": "Hi", "body": "Hello"}
    result = InputGuard.validate(args, _SCHEMA)
    assert result["to"] == "alice@example.com"


def test_missing_required_raises():
    with pytest.raises(InputGuardError, match="required"):
        InputGuard.validate({"to": "alice@example.com"}, _SCHEMA)


def test_wrong_type_raises():
    with pytest.raises(InputGuardError):
        InputGuard.validate({"to": 123, "subject": "Hi", "body": "Hello"}, _SCHEMA)


def test_pagination_defaults_injected():
    list_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "page": {"type": "integer"},
            "page_size": {"type": "integer"},
        },
        "required": ["query"],
    }
    args = {"query": "hello"}
    result = InputGuard.validate(args, list_schema)
    assert result["page"] == 1
    assert result["page_size"] == 20


def test_no_schema_passes_any_args():
    args = {"arbitrary": "data", "number": 42}
    result = InputGuard.validate(args, None)
    assert result == args


def test_empty_schema_passes():
    result = InputGuard.validate({"x": 1}, {"type": "object", "properties": {}})
    assert result["x"] == 1
