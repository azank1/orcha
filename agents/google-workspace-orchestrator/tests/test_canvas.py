"""Unit tests for the agentic CanvasKit emission helpers (pure, no live deps)."""

from __future__ import annotations

import json

from src.canvas import (
    build_data_table,
    find_table_values,
    validate_manifest,
    wrap_envelope,
)


def test_validate_manifest_accepts_valid_data_table():
    obj = {
        "version": "1.0",
        "layout": "table",
        "components": [
            {"type": "data_table", "id": "t", "columns": [{"key": "a", "label": "A"}], "rows": [{"a": 1}]}
        ],
    }
    m = validate_manifest(obj)
    assert m is not None and m["version"] == "1.0" and len(m["components"]) == 1


def test_validate_manifest_unwraps_manifest_key():
    obj = {"manifest": {"layout": "single", "components": [
        {"type": "metric_card", "id": "m", "label": "Total", "value": 42}]}}
    m = validate_manifest(obj)
    assert m is not None and m["components"][0]["type"] == "metric_card"


def test_validate_manifest_drops_unknown_type_and_missing_fields():
    obj = {"layout": "dashboard", "components": [
        {"type": "wormhole", "id": "x"},                       # unknown type -> dropped
        {"type": "metric_card", "id": "m"},                    # missing label/value -> dropped
        {"type": "data_table", "id": "d", "columns": {}, "rows": []},  # columns not a list -> dropped
        {"type": "metric_card", "id": "ok", "label": "N", "value": 1},  # valid -> kept
    ]}
    m = validate_manifest(obj)
    assert m is not None and len(m["components"]) == 1 and m["components"][0]["id"] == "ok"


def test_validate_manifest_synthesizes_missing_id():
    obj = {"components": [{"type": "metric_card", "label": "N", "value": 1}]}
    m = validate_manifest(obj)
    assert m is not None and isinstance(m["components"][0]["id"], str) and m["components"][0]["id"]


def test_validate_manifest_none_when_nothing_valid():
    assert validate_manifest({"components": [{"type": "nope"}]}) is None
    assert validate_manifest({"manifest": None}) is None
    assert validate_manifest("not a dict") is None
    assert validate_manifest({"components": "notalist"}) is None


def test_validate_manifest_coerces_bad_layout():
    m = validate_manifest({"layout": "hologram", "components": [
        {"type": "metric_card", "id": "m", "label": "N", "value": 1}]})
    assert m is not None and m["layout"] == "dashboard"


def test_build_data_table_maps_header_and_rows():
    values = [["Name", "Age"], ["Ada", 36], ["Alan", 41]]
    m = build_data_table(values, title="People")
    assert m is not None
    comp = m["components"][0]
    assert comp["type"] == "data_table"
    assert [c["key"] for c in comp["columns"]] == ["Name", "Age"]
    assert comp["rows"] == [{"Name": "Ada", "Age": 36}, {"Name": "Alan", "Age": 41}]
    assert m["layout"] == "table"


def test_build_data_table_caps_rows():
    values = [["n"]] + [[i] for i in range(500)]
    m = build_data_table(values, max_rows=10)
    assert m is not None and len(m["components"][0]["rows"]) == 10


def test_build_data_table_none_on_empty():
    assert build_data_table([]) is None
    assert build_data_table([[]]) is None


def test_find_table_values_direct_and_nested_and_json_string():
    grid = [["h"], ["v"]]
    assert find_table_values({"values": grid}) == grid
    assert find_table_values({"content": [{"text": json.dumps({"values": grid})}]}) == grid
    assert find_table_values(grid) == grid
    assert find_table_values({"nothing": 1}) is None


def test_wrap_envelope_shape():
    env = json.loads(wrap_envelope({"version": "1.0", "layout": "table", "components": []}, "sum"))
    assert env["__canvas__"] is True and env["summary"] == "sum" and env["manifest"]["version"] == "1.0"
