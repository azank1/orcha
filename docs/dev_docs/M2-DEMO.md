# M2 — Demo + launch assets

Canonical spec: [SCOPE-MAP.md](SCOPE-MAP.md) § M2. Branch: `az/feat/launch-assets`.

## Demo goal (canonical)

```
Show me my portfolio performance, use your web scraper agent to summarize https://en.wikipedia.org/wiki/Nvidia, and screenshot the Alpaca dashboard
```

**Expected routing (genuinely 3 protocol families, verified live):**

| Step | Protocol | Agent |
|------|----------|-------|
| Portfolio dashboard | MCP | `finance-dashboard-agent` → CanvasKit |
| Company summary | A2A | `web-scraper` (`delegate__did_orcha_agent_web-scraper`) |
| Screenshot | COMPUTER_USE | `MockComputerUseBackend` |

The goal names the agent explicitly ("your web scraper agent") because the
orchestrator's tool list also contains an unconfigured system Firecrawl tool
that shares the "web-scraper" name — without the explicit phrasing the LLM
picks that broken tool instead (see `scripts/m2-gates-live.sh`'s
`a2a_web_scraper` check, which asserts the specific `delegate__` tool name).

## Validation protocol

1. Run the goal **5 times** on a live stack (sandbox or `run-all.sh`).
2. **Pass:** ≥4/5 runs invoke all three protocol families and emit `canvas_manifest`.
3. **Wall clock:** target &lt;30s per run (record best take for hero clip).

```bash
# After stack is up and agents seeded:
./scripts/m2-demo-validate.sh

# Automated SSE check (single run or 5-run protocol):
GATEWAY_URL=http://localhost/api ./scripts/m2-gates-live.sh
GATEWAY_URL=http://localhost/api M2_RUNS=5 M2_PASS=4 ./scripts/m2-gates-live.sh
```

## Hero clip must show

- One goal typed → routing visible in progress stream
- 3-protocol composition in one run (MCP + A2A + COMPUTER_USE — not MCP twice)
- CanvasKit dashboard (not plain text reply)
- Under 30 seconds wall clock

## Launch checklist

- [ ] Hero GIF/MP4 (&lt;5MB) embedded in README
- [ ] README above-fold = working runtime (DAPN in ROADMAP only)
- [ ] Show HN draft: problem → demo → `emerge init` CTA
- [ ] One-screen landing → sandbox URL
- [ ] Discord announced
