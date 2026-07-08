"""Agentic CanvasKit emission for the Workspace orchestrator.

The agent's LLM composes a `UIManifest` from the vetted CanvasKit catalog based on
the actual data it read (KPI -> metric_card, series -> line_chart, rows -> data_table),
rather than a hardcoded per-tool template. `validate_manifest` is the emission-side
fail-closed guard: it drops any component whose type is unknown or whose required
fields are missing, mirroring the frontend renderer's `default: null`. If the LLM
produces nothing valid, callers fall back to a deterministic `data_table` (for
tabular results) and finally to plain text — so output is never worse than today.

Catalog kept in sync with frontend/src/types/canvas.ts (CanvasKit v0.1).
"""

from __future__ import annotations

import json
from typing import Any

# Layouts accepted by the frontend (canvas.ts CanvasLayout).
_LAYOUTS = {"dashboard", "single", "table", "timeline"}

# Required fields per component type (beyond `type` + `id`), and which of those
# must be JSON arrays. Kept aligned with the *Spec interfaces in canvas.ts.
_REQUIRED: dict[str, list[str]] = {
    "metric_card": ["label", "value"],
    "line_chart": ["x_key", "y_keys", "data"],
    "data_table": ["columns", "rows"],
    "alert_feed": ["alerts"],
    "pie_chart": ["data"],
    "stat_grid": ["stats"],
    "progress_bar": ["label", "value"],
    "timeline": ["events"],
}
_ARRAY_FIELDS = {
    "y_keys", "data", "columns", "rows", "alerts", "stats", "events",
}

# Compact catalog description injected into the render LLM prompt.
CATALOG_PROMPT = """CanvasKit components (choose only from these; fill fields exactly):
- metric_card: {type,id,label,value,unit?,delta?,trend?('up'|'down'|'flat'),sub_label?}
- line_chart: {type,id,title?,x_key,y_keys:[string],data:[{...}],colors?}
- data_table: {type,id,title?,columns:[{key,label,type?('text'|'number'|'currency'|'date'|'percent')}],rows:[{...}]}
- alert_feed: {type,id,title?,alerts:[{id,severity('info'|'warning'|'error'|'success'),title,body?,timestamp?}]}
- pie_chart: {type,id,title?,data:[{label,value,color?}]}
- stat_grid: {type,id,columns?(2|3|4),stats:[{label,value,delta?,unit?}]}
- progress_bar: {type,id,label,value,max?,color?('default'|'success'|'warning'|'error')}
- timeline: {type,id,title?,events:[{id,label,timestamp?,description?,status?('complete'|'active'|'pending')}]}"""

RENDER_INSTRUCTION = (
    "You turn Google Workspace tool results into a CanvasKit UIManifest for a dashboard UI.\n"
    "Output ONLY valid JSON (no markdown fences), shape:\n"
    '{"version":"1.0","title":"<short>","layout":"dashboard"|"single"|"table"|"timeline",'
    '"components":[<one or more components>]}\n\n'
    + CATALOG_PROMPT
    + "\n\nRules:\n"
    "- Pick the components that best represent THIS data: tabular rows -> data_table; a "
    "numeric time/date series -> line_chart; a single headline number -> metric_card; parts "
    "of a whole -> pie_chart. Combine when useful (e.g. a metric_card summary + a data_table).\n"
    "- Every component needs a unique string id and all its required fields.\n"
    "- Do NOT invent component types or fields outside the catalog.\n"
    '- If nothing visual fits the data, output exactly {"manifest":null}.'
)


def validate_manifest(obj: Any) -> dict[str, Any] | None:
    """Return a clean UIManifest dict, or None if nothing valid survives.

    Coerces version to "1.0" and layout to a known value (we own emission), drops
    components with unknown type / missing required fields / wrong array shapes, and
    synthesizes a component id when the LLM omits one.
    """
    if isinstance(obj, dict) and isinstance(obj.get("manifest"), dict):
        # LLM may wrap as {"manifest": {...}} — unwrap.
        obj = obj["manifest"]
    if not isinstance(obj, dict):
        return None

    components_in = obj.get("components")
    if not isinstance(components_in, list):
        return None

    layout = obj.get("layout")
    if layout not in _LAYOUTS:
        layout = "dashboard"

    valid: list[dict[str, Any]] = []
    for idx, comp in enumerate(components_in):
        if not isinstance(comp, dict):
            continue
        ctype = comp.get("type")
        required = _REQUIRED.get(ctype)
        if required is None:
            continue
        ok = True
        for field in required:
            val = comp.get(field)
            if val is None or val == "":
                ok = False
                break
            if field in _ARRAY_FIELDS and not isinstance(val, list):
                ok = False
                break
        if not ok:
            continue
        if not isinstance(comp.get("id"), str) or not comp["id"]:
            comp["id"] = f"c{idx}"
        valid.append(comp)

    if not valid:
        return None

    manifest: dict[str, Any] = {"version": "1.0", "layout": layout, "components": valid}
    title = obj.get("title")
    if isinstance(title, str) and title:
        manifest["title"] = title
    return manifest


def find_table_values(raw: Any, _depth: int = 0) -> list[list[Any]] | None:
    """Best-effort search for a Google Sheets `values` array (list of lists).

    Handles MCP wrapping: nested dicts/lists and JSON encoded inside text blobs.
    """
    if _depth > 6:
        return None
    if isinstance(raw, str):
        try:
            return find_table_values(json.loads(raw), _depth + 1)
        except (json.JSONDecodeError, TypeError, ValueError):
            return None
    if isinstance(raw, dict):
        vals = raw.get("values")
        if isinstance(vals, list) and vals and all(isinstance(r, list) for r in vals):
            return vals
        for v in raw.values():
            found = find_table_values(v, _depth + 1)
            if found:
                return found
        return None
    if isinstance(raw, list):
        # A bare list-of-lists is itself a values grid.
        if raw and all(isinstance(r, list) for r in raw):
            return raw
        for item in raw:
            found = find_table_values(item, _depth + 1)
            if found:
                return found
    return None


def build_data_table(values: list[list[Any]], title: str = "Sheet", max_rows: int = 200) -> dict[str, Any] | None:
    """Deterministic fallback: header row -> columns, remaining rows -> rows."""
    if not isinstance(values, list) or not values or not isinstance(values[0], list):
        return None
    header = [str(h) for h in values[0]]
    if not header:
        return None
    columns = [
        {"key": (h or f"col{i}"), "label": (h or f"Column {i + 1}")}
        for i, h in enumerate(header)
    ]
    keys = [c["key"] for c in columns]
    rows: list[dict[str, Any]] = []
    for raw_row in values[1 : max_rows + 1]:
        if not isinstance(raw_row, list):
            continue
        rows.append({keys[i]: (raw_row[i] if i < len(raw_row) else "") for i in range(len(keys))})
    return {
        "version": "1.0",
        "title": title,
        "layout": "table",
        "components": [{"type": "data_table", "id": "sheet", "columns": columns, "rows": rows}],
    }


def wrap_envelope(manifest: dict[str, Any], summary: str = "") -> str:
    """Wrap a manifest in the `__canvas__` envelope the OutputNormalizer detects."""
    return json.dumps({"__canvas__": True, "summary": summary, "manifest": manifest})
