# Launch assets (canonical home)

This is the primary space for OSS launch assets. Keep designs, web
templates, post language, and content here.

| Path | Contents | Public? |
|---|---|---|
| `brand/` | Orcha logo kit — icon / lockup / glyph, PNG + SVG | ✅ safe for public repo |
| `discord/` | Server icon, banner, welcome card | ✅ safe |
| `templates/` | `landing.html` (landing design source — shipped version lives in `deploy/landing/index.html`), `logo.html` (logo showcase) | ✅ safe |
| `launch/` | **Marketing ops** — content kit, post language, calendars, reply templates | ❌ **internal only — never export** |

**Export rule:** `docs/assets/launch/` must never cross into the public repo.
Reply templates and posting calendars in public view read as astroturfing.
When running the public export, exclude this directory.

Related: `global-feat-oss/` holds external idea/trend inputs (newsletter
PDFs etc.) — also internal only.

## Demo clip (`demo-hero.gif`) — re-record before launch

The old `demo-hero.gif` was removed (stale — recorded 2026-06-27, predates
the genuinely 3-protocol demo goal). Re-record against the hardened stack
(see ROADMAP v0.2.0). **Target:** <5MB, <30s wall clock.

Use the **3-protocol demo** goal from [`scripts/m2-demo-goal.txt`](../../scripts/m2-demo-goal.txt):

> Show me my portfolio performance, use your web scraper agent to summarize https://en.wikipedia.org/wiki/Nvidia, and screenshot the Alpaca dashboard

The clip should show:

1. Goal typed (Home or Chat)
2. Tool timeline: finance-dashboard (MCP) + web-scraper (A2A) + computer-use (COMPUTER_USE)
3. CanvasKit dashboard rendering (metric cards, chart, table, alerts)
4. Total runtime under ~30 seconds — verified live at 13-15s across 5/5 runs

Record with OBS, Peek, or similar at 1280×720 against the sandbox stack
(`make -f deploy/sandbox/Makefile up && make -f deploy/sandbox/Makefile seed`).
Export GIF:

```bash
ffmpeg -i demo-hero.mp4 -vf "fps=12,scale=1280:-1:flags=lanczos" -loop 0 docs/assets/demo-hero.gif
gifsicle -O3 --colors 128 -o docs/assets/demo-hero.gif docs/assets/demo-hero.gif  # compress if needed
```
