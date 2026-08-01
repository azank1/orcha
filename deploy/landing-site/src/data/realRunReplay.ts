// REAL run replay — captured from the live sandbox, 2026-08-01.
// Session fe55a302-69da-4fa5-a2a6-ea9a1c9dcc66. Every line below came from the actual SSE stream of that run
// (portfolio + web-scraper + computer-use hero goal). Do not edit by hand —
// recapture with scripts/e2e-launch-verify.sh + distillation instead.
export interface ReplayLine { t: string; cls?: 'cmd' | 'ok' | 'cm'; d: number }

export const CAPTURED_AT = "2026-08-01";

export const REAL_RUN_REPLAY: ReplayLine[] = [
{ t: "# goal: portfolio + nvidia summary + screenshot", cls: "cm", d: 900 },
{ t: "  ⠿ planning… 3 steps detected", cls: "cm", d: 1100 },
{ t: "  ✓ finance-dashboard · MCP · verified", cls: "ok", d: 800 },
{ t: "  ✓ web-scraper · A2A · verified", cls: "ok", d: 800 },
{ t: "  ✓ computer-use-agent · COMPUTER_USE · verified", cls: "ok", d: 800 },
{ t: "  ✓ search-agent · MCP · verified", cls: "ok", d: 800 },
{ t: "  ✓ canvas_manifest → dashboard rendered", cls: "ok", d: 600 },
{ t: "  ✓ 3 protocols · verified · settled (mock) · 28s", cls: "ok", d: 0 },
]
