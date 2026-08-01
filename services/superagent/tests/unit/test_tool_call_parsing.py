from __future__ import annotations

from superagent.tool_call_parsing import (
    normalize_openai_api_tool_calls,
    normalize_stream_tool_calls,
)


def test_normalize_stream_tool_calls_unwraps_json_string_args():
    raw = [
        {
            "id": "call_1",
            "name": "docs_append",
            "args": {"content": '["line1", "line2"]', "doc_id": "abc"},
        }
    ]
    out = normalize_stream_tool_calls(raw, model_name="anthropic/claude-sonnet")
    assert out[0]["id"] == "call_1"
    assert out[0]["name"] == "docs_append"
    assert out[0]["args"]["content"] == ["line1", "line2"]
    assert out[0]["args"]["doc_id"] == "abc"


def test_normalize_openai_api_tool_calls_parses_function_arguments():
    raw = [
        {
            "id": "call_2",
            "type": "function",
            "function": {
                "name": "sheets_write",
                "arguments": '{"range_notation":"Sheet1!A1","values":[["a","b"]]}',
            },
        }
    ]
    out = normalize_openai_api_tool_calls(raw)
    assert out is not None
    assert out[0]["name"] == "sheets_write"
    assert out[0]["args"]["range_notation"] == "Sheet1!A1"
    assert out[0]["args"]["values"] == [["a", "b"]]
