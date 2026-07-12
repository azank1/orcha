# Demo assets (M2)

## `demo-hero.gif`

Hero clip for README and Show HN. **Target:** &lt;5MB, &lt;30s wall clock in the recording.

**Status: the current `demo-hero.gif` is stale (recorded 2026-06-27) and
must be re-recorded before launch.** It predates the fix that made the demo
goal genuinely 3-protocol (see `docs/dev_docs/M0-VERIFICATION.md`) — the old
goal only exercised MCP twice + COMPUTER_USE, not MCP + A2A + COMPUTER_USE.
Recording requires real screen-capture software against a live browser
session; it cannot be automated by an agent.

### What to capture

Use the **3-protocol demo** goal from [`scripts/m2-demo-goal.txt`](../../scripts/m2-demo-goal.txt):

> Show me my portfolio performance, use your web scraper agent to summarize https://en.wikipedia.org/wiki/Nvidia, and screenshot the Alpaca dashboard

The clip should show:

1. Goal typed (Home or Chat)
2. Tool timeline: finance-dashboard (MCP) + web-scraper (A2A, `delegate__did_orcha_agent_web-scraper`) + computer-use (COMPUTER_USE)
3. CanvasKit dashboard rendering (metric cards, chart, table, alerts)
4. Total runtime under ~30 seconds — verified live at 13-15s across 5/5 runs

### Record

```bash
# Stack up
make -f deploy/sandbox/Makefile up
make -f deploy/sandbox/Makefile seed

# Optional: validate before recording
GATEWAY_URL=http://localhost/api M2_RUNS=5 M2_PASS=4 ./scripts/m2-gates-live.sh
```

Record with OBS, Peek, or similar at 1280×720. Export GIF:

```bash
ffmpeg -i demo-hero.mp4 -vf "fps=12,scale=1280:-1:flags=lanczos" -loop 0 docs/assets/demo-hero.gif
# compress if needed:
gifsicle -O3 --colors 128 -o docs/assets/demo-hero.gif docs/assets/demo-hero.gif
```

Replace the placeholder `demo-hero.gif` in this directory before Show HN.
