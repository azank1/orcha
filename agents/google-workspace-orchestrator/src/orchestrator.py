"""DAG planner + MCP execution (OpenRouter via ADK)."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from .adk_llm import complete_llm
from .agent_registry import PLANNER_DOMAIN_IDS, tools_for_domain
from .canvas import (
    RENDER_INSTRUCTION,
    build_data_table,
    find_table_values,
    validate_manifest,
    wrap_envelope,
)
from .config import Settings
from .hitl import hitl_message, tool_requires_hitl
from .mcp_client import WorkspaceMCPClient

logger = logging.getLogger(__name__)

_PLANNER_AGENT_ENUM = "|".join(PLANNER_DOMAIN_IDS)
_PLANNER_INSTRUCTION = f"""You are a workspace task planner. Output ONLY valid JSON (no markdown fences).
Schema: {{"steps":[{{"id":"string","agent":"{_PLANNER_AGENT_ENUM}","goal":"string","depends_on":["optional_step_ids"]}}]}}
Use 1-8 steps. Choose the minimal domain agents needed. Each agent maps to workspace-mcp tool groups (Calendar, Drive, Gmail, Docs, Sheets, Slides, Forms, Tasks, Contacts, Chat, Custom Search, Apps Script)."""

_TOOL_PICKER_PREFIX = """You pick ONE MCP tool call for Google Workspace.
Output ONLY valid JSON (no markdown, no explanation):
{"tool_name":"<exact tool name>","arguments":{<key:value pairs matching the schema exactly>}}

Rules:
- Copy the tool name EXACTLY as shown.
- Include ALL required fields listed in the schema.
- Use the exact types: strings must be strings (not arrays), arrays must be arrays.
- If a field is marked required, you MUST include it even if you have to infer a value from the goal.
- Do NOT include unknown fields."""


def _format_tool_schemas(tools: list[dict[str, Any]]) -> str:
    """
    Render a compact schema block for the tool picker LLM.

    For each tool produces:
        send_gmail_message — Send an email
          required: user_google_email (string), to (string), subject (string), body (string)
          optional: cc (string), bcc (string)

    This gives the LLM enough information to generate correct argument types and
    not omit required fields — the root cause of validation errors like
    "user_google_email: Missing required argument" and "to: expected string, got array".
    """
    lines: list[str] = []
    for tool in tools:
        name = tool.get("name", "")
        desc = (tool.get("description") or "").split("\n")[0][:100]
        schema: dict[str, Any] = tool.get("inputSchema") or tool.get("input_schema") or {}
        props: dict[str, Any] = schema.get("properties") or {}
        required_set: set[str] = set(schema.get("required") or [])

        if not name:
            continue
        lines.append(f"\n{name} — {desc}" if desc else f"\n{name}")

        req_parts: list[str] = []
        opt_parts: list[str] = []
        for field, fschema in props.items():
            ftype = fschema.get("type", "any")
            fdesc = (fschema.get("description") or "").split(".")[0][:60]
            entry = f"{field} ({ftype})" + (f": {fdesc}" if fdesc else "")
            if field in required_set:
                req_parts.append(entry)
            else:
                opt_parts.append(entry)

        if req_parts:
            lines.append(f"  required: {', '.join(req_parts)}")
        if opt_parts:
            lines.append(f"  optional: {', '.join(opt_parts)}")

    return "\n".join(lines)


def _extract_json_object(text: str) -> dict[str, Any] | None:
    text = text.strip()
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def _toposort(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pending = {s["id"]: s for s in steps if s.get("id")}
    order: list[dict[str, Any]] = []
    while pending:
        ready = [
            sid
            for sid, s in pending.items()
            if all(d in {x["id"] for x in order} for d in (s.get("depends_on") or []) if d)
        ]
        if not ready:
            order.extend(pending.values())
            break
        for sid in ready:
            order.append(pending.pop(sid))
    return order


async def run_workspace_task(
    settings: Settings,
    mcp: WorkspaceMCPClient,
    bearer: str | None,
    user_query: str,
    resume_hitl: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Returns a dict with keys: text (str), hitl (optional dict for input-required)."""
    if resume_hitl and resume_hitl.get("pending_tool"):
        approved = resume_hitl.get("user_said_approve")
        if approved:
            raw = await mcp.tools_call(
                resume_hitl["pending_tool"],
                resume_hitl.get("pending_args") or {},
                bearer,
            )
            summary = json.dumps(raw, indent=2)
            return {"text": f"Executed after approval:\n{summary}"}

    tools = await mcp.tools_list(bearer)
    if not tools:
        return {"text": "No MCP tools available. Is workspace-mcp running and authenticated?"}

    plan_raw = await complete_llm(
        settings,
        _PLANNER_INSTRUCTION,
        f"User request:\n{user_query}",
    )
    plan = _extract_json_object(plan_raw) or {}
    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps:
        steps = [
            {
                "id": "s1",
                "agent": "workspace_orchestrator",
                "goal": user_query,
                "depends_on": [],
            }
        ]

    context_chunks: list[str] = []
    raw_results: list[dict[str, Any]] = []
    for step_idx, step in enumerate(_toposort([s for s in steps if isinstance(s, dict)])):
        agent = str(step.get("agent") or "workspace_orchestrator")
        goal = str(step.get("goal") or user_query)
        step_id = str(step.get("id") or f"step_{step_idx}")
        logger.info(
            "orchestrator_step step=%s agent=%s goal_preview=%s",
            step_id,
            agent,
            goal[:120],
        )
        if agent == "workspace_orchestrator":
            domain_tools = tools
        else:
            domain_tools = tools_for_domain(agent, tools)
        tool_schema_lines = _format_tool_schemas(domain_tools[:40])
        picker_prompt = (
            f"{_TOOL_PICKER_PREFIX}\n\nAvailable tools (name + schema):\n"
            + tool_schema_lines
            + f"\n\nPrior step results:\n{chr(10).join(context_chunks[-3:]) or 'none'}"
            + f"\n\nGoal:\n{goal}"
        )
        logger.debug("orchestrator_picker_prompt step=%s:\n%s", step_id, picker_prompt[:2000])
        pick_raw = await complete_llm(settings, picker_prompt, goal)
        logger.info("orchestrator_pick_raw step=%s raw=%s", step_id, pick_raw[:600])
        pick = _extract_json_object(pick_raw) or {}
        tool_name = str(pick.get("tool_name") or "").strip()
        arguments = pick.get("arguments")
        if not tool_name or not isinstance(arguments, dict):
            logger.warning(
                "orchestrator_tool_pick_failed step=%s agent=%s raw=%s",
                step_id,
                agent,
                pick_raw[:400],
            )
            context_chunks.append(f"[{agent}] Could not map goal to a tool. Raw: {pick_raw[:800]}")
            continue
        logger.info(
            "orchestrator_tool_picked step=%s agent=%s tool=%s args=%s hitl=%s",
            step_id,
            agent,
            tool_name,
            json.dumps(arguments, default=str)[:400],
            tool_requires_hitl(tool_name),
        )
        if tool_requires_hitl(tool_name):
            return {
                "text": "",
                "hitl": {
                    "pending_tool": tool_name,
                    "pending_args": arguments,
                    "message": hitl_message(tool_name),
                },
            }
        raw = await mcp.tools_call(tool_name, arguments, bearer)
        raw_results.append({"tool": tool_name, "raw": raw})
        snippet = json.dumps(raw, indent=2)[:4000]
        logger.info("orchestrator_step_done step=%s tool=%s snippet_len=%d", step_id, tool_name, len(snippet))
        context_chunks.append(f"[{agent}] {tool_name}: {snippet}")

    if not context_chunks:
        return {"text": "No steps produced a result. Try a more specific request."}

    summary = await complete_llm(
        settings,
        "Summarize the following workspace tool results for the user. Be concise and actionable.",
        "\n\n".join(context_chunks),
    )
    summary = summary or ""

    # Agentic CanvasKit render: the LLM composes a manifest from the vetted catalog
    # based on the actual data (validated, fail-closed). Fall back to a deterministic
    # data_table for tabular results, then to plain text — never worse than today.
    manifest = await _render_manifest(settings, raw_results)
    if manifest is None:
        for item in raw_results:
            values = find_table_values(item.get("raw"))
            if values:
                manifest = build_data_table(values, title=str(item.get("tool") or "Sheet"))
                if manifest is not None:
                    break
    if manifest is not None:
        return {"text": wrap_envelope(manifest, summary or "Rendered workspace result.")}
    return {"text": summary or "\n\n".join(context_chunks)}


def _compact_results(raw_results: list[dict[str, Any]], max_chars: int = 6000) -> str:
    """Size-bounded view of raw tool outputs for the render LLM."""
    if not raw_results:
        return ""
    budget = max(500, max_chars // len(raw_results))
    parts: list[str] = []
    for item in raw_results:
        text = json.dumps(item.get("raw"), default=str)
        if len(text) > budget:
            text = text[:budget] + "…(truncated)"
        parts.append(f"[{item.get('tool', '')}]\n{text}")
    return "\n\n".join(parts)[:max_chars]


async def _render_manifest(
    settings: Settings, raw_results: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Ask the LLM to compose a CanvasKit manifest from the tool results; validate it."""
    if not raw_results:
        return None
    try:
        raw = await complete_llm(settings, RENDER_INSTRUCTION, _compact_results(raw_results))
    except Exception:
        logger.exception("canvas_render_llm_failed")
        return None
    obj = _extract_json_object(raw)
    if obj is None:
        return None
    manifest = validate_manifest(obj)
    logger.info("canvas_render manifest_valid=%s", manifest is not None)
    return manifest
