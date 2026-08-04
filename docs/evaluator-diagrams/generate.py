#!/usr/bin/env python3
"""Regenerate evaluator Excalidraw diagrams (visual flow + concise technical copy).

Rectangle ``label`` JSON is not rendered by many Excalidraw importers; we emit
separate ``text`` elements with width/height/fontFamily and bind them to shapes.
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent

CAM_W, CAM_H = 1240, 880


def camera() -> dict:
    return {"type": "cameraUpdate", "width": CAM_W, "height": CAM_H, "x": 0, "y": 0}


def _base_text(
    eid: str,
    x: float,
    y: float,
    width: float,
    height: float,
    content: str,
    font_size: int,
    stroke_color: str,
    text_align: str,
    vertical_align: str,
    container_id: str | None,
) -> dict:
    return {
        "type": "text",
        "version": 1,
        "versionNonce": abs(hash(eid)) % 1_000_000 + 1,
        "isDeleted": False,
        "id": eid,
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": 100,
        "angle": 0,
        "x": x,
        "y": y,
        "strokeColor": stroke_color,
        "backgroundColor": "transparent",
        "width": width,
        "height": height,
        "seed": 1,
        "groupIds": [],
        "frameId": None,
        "roundness": None,
        "boundElements": [],
        "updated": 1,
        "link": None,
        "locked": False,
        "fontSize": font_size,
        "fontFamily": 1,
        "text": content,
        "textAlign": text_align,
        "verticalAlign": vertical_align,
        "containerId": container_id,
        "originalText": content,
        "lineHeight": 1.25,
    }


def text_el(
    eid: str,
    x: float,
    y: float,
    content: str,
    size: int = 14,
    color: str = "#111827",
    max_width: float = 900,
) -> dict:
    lines = content.split("\n")
    longest = max((len(line) for line in lines), default=1)
    width = min(max_width, max(64, int(longest * size * 0.52)))
    height = max(int(len(lines) * size * 1.35), size + 4)
    return _base_text(
        eid,
        x,
        y,
        float(width),
        float(height),
        content,
        size,
        color,
        "left",
        "top",
        None,
    )


def rect_only(
    eid: str,
    x: float,
    y: float,
    w: float,
    h: float,
    bg: str,
    stroke: str,
    stroke_width: int = 2,
    opacity: int | None = None,
) -> dict:
    return {
        "type": "rectangle",
        "version": 1,
        "versionNonce": 1,
        "isDeleted": False,
        "id": eid,
        "fillStyle": "solid",
        "strokeWidth": stroke_width,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": opacity if opacity is not None else 100,
        "angle": 0,
        "x": x,
        "y": y,
        "width": w,
        "height": h,
        "strokeColor": stroke,
        "backgroundColor": bg,
        "seed": 1,
        "groupIds": [],
        "frameId": None,
        "roundness": {"type": 3},
        "boundElements": [],
        "updated": 1,
        "link": None,
        "locked": False,
    }


def extend_labeled_rect(
    els: list[dict],
    eid: str,
    x: float,
    y: float,
    w: float,
    h: float,
    label: str,
    bg: str,
    stroke: str,
    label_size: int = 13,
    opacity: int | None = None,
) -> dict:
    """Append rectangle + centered text (no container binding — widest importer support)."""
    r = rect_only(eid, x, y, w, h, bg, stroke, opacity=opacity)
    els.append(r)
    if label.strip():
        tid = f"{eid}__lbl"
        pad_x, pad_y = 8.0, 6.0
        t = _base_text(
            tid,
            x + pad_x,
            y + pad_y,
            w - 2 * pad_x,
            h - 2 * pad_y,
            label,
            label_size,
            "#111827",
            "center",
            "middle",
            None,
        )
        els.append(t)
    return r


def arrow_abs(eid: str, x1: float, y1: float, x2: float, y2: float) -> dict:
    dx, dy = x2 - x1, y2 - y1
    return {
        "type": "arrow",
        "version": 1,
        "versionNonce": 1,
        "isDeleted": False,
        "id": eid,
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": 100,
        "angle": 0,
        "x": x1,
        "y": y1,
        "strokeColor": "#111827",
        "backgroundColor": "transparent",
        "width": dx,
        "height": dy,
        "seed": 1,
        "groupIds": [],
        "frameId": None,
        "roundness": None,
        "boundElements": [],
        "updated": 1,
        "link": None,
        "locked": False,
        "points": [[0, 0], [dx, dy]],
        "lastCommittedPoint": None,
        "startBinding": None,
        "endBinding": None,
        "startArrowhead": None,
        "endArrowhead": "arrow",
    }


def cx(box: dict) -> float:
    return float(box["x"]) + float(box["width"]) / 2


def cy(box: dict) -> float:
    return float(box["y"]) + float(box["height"]) / 2


def link_right(
    eid: str,
    left: dict,
    right: dict,
    pad: float = 6,
) -> dict:
    x1 = float(left["x"]) + float(left["width"]) + pad
    y1 = cy(left)
    x2 = float(right["x"]) - pad
    y2 = cy(right)
    return arrow_abs(eid, x1, y1, x2, y2)


def link_down(eid: str, top: dict, bottom: dict, pad: float = 8) -> dict:
    x1 = cx(top)
    y1 = float(top["y"]) + float(top["height"]) + pad
    x2 = cx(bottom)
    y2 = float(bottom["y"]) - pad
    return arrow_abs(eid, x1, y1, x2, y2)


def wrap(elements: list[dict]) -> dict:
    return {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {"viewBackgroundColor": "#ffffff", "gridSize": None},
        "files": {},
    }


def write_pair(stem: str, elements: list[dict]) -> None:
    doc = wrap(elements)
    (OUT / f"{stem}.excalidraw").write_text(json.dumps(doc, indent=2), encoding="utf-8")
    inner = json.dumps(elements, separators=(",", ":"))
    invoke = json.dumps({"elements": inner}, separators=(",", ":"))
    (OUT / f"{stem}.invoke.json").write_text(invoke, encoding="utf-8")
    print(stem, "elements", len(elements), "invoke_bytes", len(invoke))


def diagram_01() -> list[dict]:
    els: list[dict] = [
        camera(),
        text_el("t", 32, 14, "01 — Publish → runtime → settlement", 20),
        text_el("ts", 32, 42, "Process sketch — implementation-agnostic", 12, "#4b5563"),
    ]

    y0 = 72
    b_builder = extend_labeled_rect(els, "b0", 40, y0, 110, 52, "Builder", "#dbeafe", "#1d4ed8", 14)
    b_pkg = extend_labeled_rect(els, "b1", 190, y0, 130, 52, "Package\n(spec + assets)", "#e0e7ff", "#4338ca", 12)
    b_ingest = extend_labeled_rect(els, "b2", 360, y0, 150, 52, "Ingest\nvalidate · sign", "#cffafe", "#0e7490", 12)
    b_fp = extend_labeled_rect(els, "b3", 550, y0, 150, 52, "Fingerprint\nsemver / lineage", "#fef3c7", "#b45309", 12)
    b_cat = extend_labeled_rect(els, "b4", 740, y0, 140, 52, "Catalog\nLIVE", "#dcfce7", "#15803d", 14)
    els.append(link_right("e01", b_builder, b_pkg))
    els.append(link_right("e02", b_pkg, b_ingest))
    els.append(link_right("e03", b_ingest, b_fp))
    els.append(link_right("e04", b_fp, b_cat))
    els.append(text_el("l1", 40, y0 - 22, "Publish pipeline", 13, "#1f2937"))

    y1 = 200
    r_user = extend_labeled_rect(els, "r0", 40, y1, 100, 56, "End user", "#f3f4f6", "#374151", 14)
    r_sess = extend_labeled_rect(
        els, "r1", 180, y1, 150, 56, "Orchestrator\n(session graph)", "#ede9fe", "#5b21b6", 12
    )
    r_plan = extend_labeled_rect(els, "r2", 370, y1, 140, 56, "Planner\ndecompose intent", "#ffedd5", "#c2410c", 12)
    r_pool = extend_labeled_rect(
        els, "r3", 550, y1, 200, 56, "Worker agents\nMCP · A2A · HTTP", "#dcfce7", "#166534", 12
    )
    r_out = extend_labeled_rect(els, "r4", 800, y1, 150, 56, "Artifacts\n+ user reply", "#e0f2fe", "#0369a1", 12)
    els.append(link_right("e11", r_user, r_sess))
    els.append(link_right("e12", r_sess, r_plan))
    els.append(link_right("e13", r_plan, r_pool))
    els.append(link_right("e14", r_pool, r_out))
    els.append(text_el("l2", 40, y1 - 24, "Runtime path (one turn can loop)", 13, "#1f2937"))

    y2 = 320
    p0 = extend_labeled_rect(els, "p0", 40, y2, 120, 50, "User funds", "#fef9c3", "#854d0e", 13)
    p1 = extend_labeled_rect(els, "p1", 200, y2, 130, 50, "Platform fee", "#fee2e2", "#b91c1c", 13)
    p2 = extend_labeled_rect(els, "p2", 370, y2, 130, 50, "Builder royalty", "#dcfce7", "#166534", 13)
    p3 = extend_labeled_rect(els, "p3", 540, y2, 200, 50, "Settlement\nUSDC · Base L2", "#cffafe", "#0e7490", 13)
    els.append(link_right("e21", p0, p1))
    els.append(link_right("e22", p1, p2))
    els.append(link_right("e23", p2, p3))
    els.append(text_el("l3", 40, y2 - 22, "Economics (simplified)", 13, "#1f2937"))

    extend_labeled_rect(els, "lane", 28, 410, 1180, 210, "", "#f9fafb", "#9ca3af", 11, opacity=35)
    els.append(text_el("lm", 44, 418, "Per-agent observability (separate time series / labels)", 14, "#111827"))

    extend_labeled_rect(els, "m0", 48, 448, 260, 152, "Commerce agent", "#eff6ff", "#2563eb", 13)
    extend_labeled_rect(els, "m1", 330, 448, 260, 152, "Calendar agent", "#ecfdf5", "#15803d", 13)
    extend_labeled_rect(els, "m2", 612, 448, 260, 152, "Custom agent", "#fff7ed", "#c2410c", 13)

    els.append(
        text_el(
            "ms",
            60,
            478,
            "• p95 / p99 latency\n• error rate\n• run count\n• uptime probe\n• price band\n• vector + lexical ids",
            12,
        )
    )
    els.append(
        text_el(
            "mc",
            342,
            478,
            "• OAuth scope usage\n• quota breaches\n• latency\n• success ratio\n• cold-start count",
            12,
        )
    )
    els.append(
        text_el(
            "mg",
            624,
            478,
            "• token / cost proxy\n• tool fan-out\n• retries\n• embedding slice\n• policy denials",
            12,
        )
    )
    els.append(
        text_el(
            "fn",
            44,
            628,
            "Each agentId carries its own metric keys — no shared “one blob” across unrelated agents.",
            12,
            "#4b5563",
        )
    )

    return els


def diagram_02() -> list[dict]:
    els: list[dict] = [
        camera(),
        text_el("t", 32, 14, "02 — Post-publish async: indexing vs planning", 20),
        text_el("ts", 32, 42, "Two jobs, two side-effects", 12, "#4b5563"),
    ]

    extend_labeled_rect(els, "La", 32, 70, 560, 320, "", "#eff6ff", "#93c5fd", 11, opacity=40)
    extend_labeled_rect(els, "Lb", 620, 70, 588, 320, "", "#fffbeb", "#fcd34d", 11, opacity=40)
    els.append(text_el("ha", 48, 78, "Job A — discovery & embeddings", 15, "#1e3a8a"))
    els.append(text_el("hb", 636, 78, "Job B — intent → executable DAG", 15, "#92400e"))

    ya = 118
    a0 = extend_labeled_rect(els, "a0", 52, ya, 130, 48, "Catalog row\n(agentId)", "#dbeafe", "#1d4ed8", 12)
    a1 = extend_labeled_rect(els, "a1", 220, ya, 140, 48, "Queue / fan-out", "#bfdbfe", "#2563eb", 12)
    a2 = extend_labeled_rect(els, "a2", 400, ya, 150, 48, "Chunk + enrich", "#93c5fd", "#1e40af", 12)
    a3 = extend_labeled_rect(els, "a3", 52, ya + 110, 160, 52, "Embedding job\n(vector store)", "#c7d2fe", "#4338ca", 12)
    a4 = extend_labeled_rect(els, "a4", 250, ya + 110, 160, 52, "Lexical index\n(BM25 / tags)", "#a5b4fc", "#3730a3", 12)
    a5 = extend_labeled_rect(els, "a5", 448, ya + 110, 120, 52, "Link back\nagentId", "#e0e7ff", "#312e81", 12)
    els.append(link_right("ae0", a0, a1))
    els.append(link_right("ae1", a1, a2))
    els.append(link_down("ae2", a2, a3, pad=14))
    x1, y1 = float(a2["x"]) + float(a2["width"]) / 2, float(a2["y"]) + float(a2["height"]) + 14
    x2, y2 = cx(a4), float(a4["y"]) - 10
    els.append(arrow_abs("ae2b", x1, y1, x2, y2))
    els.append(arrow_abs("ae3", cx(a3), float(a3["y"]) + float(a3["height"]) + 10, float(a5["x"]) + 20, cy(a5)))
    els.append(arrow_abs("ae4", cx(a4), float(a4["y"]) + float(a4["height"]) + 10, float(a5["x"]) + 60, cy(a5)))

    yb = 118
    b0 = extend_labeled_rect(els, "b0", 640, yb, 150, 48, "Raw user intent", "#ffedd5", "#c2410c", 12)
    b1 = extend_labeled_rect(els, "b1", 820, yb, 150, 48, "Decompose\n(subtasks)", "#fed7aa", "#ea580c", 12)
    b2 = extend_labeled_rect(els, "b2", 990, yb, 170, 48, "Policy filter\nRBAC / tenant", "#fdba74", "#c2410c", 12)
    b3 = extend_labeled_rect(els, "b3", 700, yb + 110, 170, 52, "Rank + bind\nagents", "#fde68a", "#b45309", 12)
    b4 = extend_labeled_rect(els, "b4", 900, yb + 110, 150, 52, "Order steps\n(DAG)", "#fcd34d", "#d97706", 12)
    b5 = extend_labeled_rect(els, "b5", 1070, yb + 110, 120, 52, "Human gate\n(optional)", "#fecaca", "#b91c1c", 12)
    b6 = extend_labeled_rect(els, "b6", 860, yb + 210, 200, 52, "Validated plan\n→ orchestrator", "#bbf7d0", "#15803d", 13)
    els.append(link_right("be0", b0, b1))
    els.append(link_right("be1", b1, b2))
    els.append(arrow_abs("be2", cx(b2), float(b2["y"]) + float(b2["height"]) + 12, cx(b3), float(b3["y"]) - 12))
    els.append(link_right("be3", b3, b4))
    els.append(link_right("be4", b4, b5))
    els.append(arrow_abs("be5", cx(b5), float(b5["y"]) + float(b5["height"]) + 14, cx(b6), float(b6["y"]) - 14))
    els.append(
        arrow_abs(
            "be5a",
            float(b4["x"]) + float(b4["width"]) * 0.35,
            float(b4["y"]) + float(b4["height"]) + 14,
            float(b6["x"]) + float(b6["width"]) * 0.25,
            float(b6["y"]) - 14,
        )
    )

    y3 = 430
    extend_labeled_rect(els, "sa", 48, y3, 520, 88, "Job A persistence", "#e0e7ff", "#4338ca", 12)
    extend_labeled_rect(els, "sb", 600, y3, 600, 88, "Job B persistence", "#ffedd5", "#c2410c", 12)
    els.append(
        text_el(
            "sat",
            60,
            y3 + 28,
            "vectors · sparse index · agentId foreign keys · reindex cursor",
            12,
            "#312e81",
        )
    )
    els.append(
        text_el(
            "sbt",
            612,
            y3 + 28,
            "ordered steps · tool/agent bindings · pause tokens · planner version",
            12,
            "#7c2d12",
        )
    )

    return els


def diagram_03() -> list[dict]:
    els: list[dict] = [
        camera(),
        text_el("t", 32, 14, "03 — Conversational control plane (single thread)", 20),
        text_el("ts", 32, 42, "Turn loop + sidecars", 12, "#4b5563"),
    ]

    y = 120
    n0 = extend_labeled_rect(els, "n0", 60, y, 140, 56, "Ingest turn\n+ memory", "#ede9fe", "#5b21b6", 12)
    n1 = extend_labeled_rect(els, "n1", 240, y, 140, 56, "Plan delta\n(tool graph)", "#ffedd5", "#c2410c", 12)
    n2 = extend_labeled_rect(els, "n2", 420, y, 170, 56, "Execute\nMCP · A2A · code", "#dcfce7", "#166534", 12)
    n3 = extend_labeled_rect(els, "n3", 630, y, 150, 56, "Trace + receipts\n(structured)", "#e0f2fe", "#0369a1", 12)
    n4 = extend_labeled_rect(els, "n4", 820, y, 150, 56, "Compose\nuser-visible reply", "#f3f4f6", "#374151", 13)
    els.append(link_right("ne0", n0, n1))
    els.append(link_right("ne1", n1, n2))
    els.append(link_right("ne2", n2, n3))
    els.append(link_right("ne3", n3, n4))

    y_band = y + 92
    x_from = float(n4["x"]) + 24
    x_to = float(n0["x"]) + float(n0["width"]) - 24
    els.append(arrow_abs("loop", x_from, y_band, x_to, y_band))
    els.append(
        text_el(
            "lp",
            (x_from + x_to) / 2 - 120,
            y_band + 10,
            "Next user / tool message re-enters the loop (same thread)",
            12,
            "#6b7280",
        )
    )

    s1 = extend_labeled_rect(els, "s1", 60, 300, 260, 110, "External systems", "#f9fafb", "#6b7280", 13)
    s2 = extend_labeled_rect(els, "s2", 360, 300, 260, 110, "Hard stops", "#fef2f2", "#b91c1c", 13)
    s3 = extend_labeled_rect(els, "s3", 660, 300, 320, 110, "What gets persisted", "#ecfdf5", "#15803d", 13)
    els.append(
        text_el(
            "s1t",
            72,
            332,
            "OAuth providers\nMCP hosts · remote APIs\nobject storage",
            12,
            "#374151",
        )
    )
    els.append(
        text_el(
            "s2t",
            372,
            332,
            "Consent screens\nsecret elevation\nhuman review queue",
            12,
            "#7f1d1d",
        )
    )
    els.append(
        text_el(
            "s3t",
            672,
            332,
            "message DAG · tool receipts\nfile pointers · correlation ids\nreplay-safe spans",
            12,
            "#14532d",
        )
    )

    els.append(
        arrow_abs(
            "c1",
            float(n2["x"]) + 48,
            float(n2["y"]) + float(n2["height"]) + 6,
            cx(s1) + 10,
            float(s1["y"]) - 4,
        )
    )
    els.append(
        arrow_abs(
            "c2",
            cx(n2),
            float(n2["y"]) + float(n2["height"]) + 6,
            cx(s2),
            float(s2["y"]) - 4,
        )
    )
    els.append(
        arrow_abs(
            "c3",
            float(n2["x"]) + float(n2["width"]) - 48,
            float(n2["y"]) + float(n2["height"]) + 6,
            cx(s3) - 10,
            float(s3["y"]) - 4,
        )
    )

    els.append(
        text_el(
            "fn",
            60,
            440,
            "Share: open the Excalidraw view in the browser from the widget when you need a static snapshot.",
            12,
            "#6b7280",
        )
    )

    return els


def main() -> None:
    write_pair("01-e2e-overview", diagram_01())
    write_pair("02-pnd-two-flows", diagram_02())
    write_pair("03-superagent-runtime", diagram_03())


if __name__ == "__main__":
    main()
