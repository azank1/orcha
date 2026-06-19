"""Provider-aware tool-call argument normalization helpers."""

from __future__ import annotations

import json
from typing import Any, Protocol


class ToolCallArgsStrategy(Protocol):
    def normalize_args(self, args: dict[str, Any]) -> dict[str, Any]: ...


class DefaultArgsStrategy:
    """Default strategy: unwrap top-level JSON strings into native values."""

    def normalize_args(self, args: dict[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        for key, value in args.items():
            if isinstance(value, str) and value.strip()[:1] in ("{", "["):
                try:
                    normalized[key] = json.loads(value)
                    continue
                except json.JSONDecodeError:
                    pass
            normalized[key] = value
        return normalized


def _strategy_for_model(model_name: str | None) -> ToolCallArgsStrategy:
    # Future extension point for provider/model-specific parsing differences.
    _ = model_name
    return DefaultArgsStrategy()


def normalize_args(
    args: dict[str, Any] | None,
    *,
    model_name: str | None = None,
) -> dict[str, Any]:
    if not isinstance(args, dict):
        return {}
    return _strategy_for_model(model_name).normalize_args(args)


def normalize_stream_tool_calls(
    raw_tool_calls: Any,
    *,
    model_name: str | None = None,
) -> list[dict[str, Any]]:
    if not isinstance(raw_tool_calls, list):
        return []
    out: list[dict[str, Any]] = []
    for tc in raw_tool_calls:
        if isinstance(tc, dict):
            tid = str(tc.get("id", "") or "")
            name = str(tc.get("name", "") or "")
            args = tc.get("args", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args or "{}")
                except Exception:
                    args = {"raw": args}
            out.append(
                {
                    "id": tid,
                    "name": name,
                    "args": normalize_args(args, model_name=model_name),
                }
            )
            continue

        tid = str(getattr(tc, "id", "") or "")
        name = str(getattr(tc, "name", "") or "")
        args = getattr(tc, "args", {}) or {}
        out.append(
            {
                "id": tid,
                "name": name,
                "args": normalize_args(args, model_name=model_name),
            }
        )
    return out


def normalize_openai_api_tool_calls(
    raw_tool_calls: Any,
    *,
    model_name: str | None = None,
) -> list[dict[str, Any]] | None:
    """OpenAI API style tool-calls -> internal tool-call list."""
    if not isinstance(raw_tool_calls, list) or not raw_tool_calls:
        return None

    out: list[dict[str, Any]] = []
    for item in raw_tool_calls:
        if not isinstance(item, dict):
            continue
        tid = str(item.get("id", "") or "")
        name = ""
        args: dict[str, Any] = {}
        fn = item.get("function")
        if isinstance(fn, dict):
            name = str(fn.get("name", "") or "")
            arg_value = fn.get("arguments")
            if isinstance(arg_value, str):
                try:
                    parsed = json.loads(arg_value)
                    if isinstance(parsed, dict):
                        args = parsed
                except json.JSONDecodeError:
                    args = {}
            elif isinstance(arg_value, dict):
                args = arg_value
        else:
            name = str(item.get("name", "") or "")
            plain_args = item.get("args")
            if isinstance(plain_args, dict):
                args = plain_args
        if name or tid:
            out.append(
                {
                    "id": tid,
                    "name": name,
                    "args": normalize_args(args, model_name=model_name),
                }
            )

    return out or None
