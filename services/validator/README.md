# validator (experimental)

> **Status: experimental spike.** Not part of the supported runtime. See
> [ROADMAP.md](../docs/ROADMAP.md) — network-layer capabilities graduate only
> after real adoption of the core runtime.

The validator is the reference implementation of an `ExecutionObserver`:
it plugs into the SuperAgent middleware seam
(`services/superagent/src/superagent/middleware/pipeline.py`) and records
per-step fulfillment records (`FulfillmentRecorder`) with Ed25519-signed
attestations.

The OSS runtime ships a `NoOpObserver` in that seam by default. This package
shows what an observer *can* do — it is the extension point a future network
layer would build on, not a live network component.

```bash
cd services/validator && uv sync && uv run pytest
```
