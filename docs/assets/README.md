# Demo assets (M2)

## `demo-hero.gif`

Hero clip for README and Show HN. **Target:** &lt;5MB, &lt;30s wall clock in the recording.

### What to capture

Use the **3-protocol demo** goal from [`scripts/m2-demo-goal.txt`](../../scripts/m2-demo-goal.txt):

> Show me my portfolio performance, search for NVDA earnings coverage, and screenshot the Alpaca dashboard

The clip should show:

1. Goal typed (Home or Chat)
2. Tool timeline: finance-dashboard + search + computer-use
3. CanvasKit dashboard rendering (metric cards, chart, table, alerts)
4. Total runtime under ~30 seconds

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
