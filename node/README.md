# emerge-node (experimental)

> **Status: experimental spike.** Not part of the supported runtime. See
> [ROADMAP.md](../ROADMAP.md) — network-layer capabilities graduate only
> after real adoption of the core runtime.

`emerge-node` is an early prototype of a gossip sidecar for agent networks:
Ed25519 signed manifest envelopes and a minimal TCP gossip transport that
lets two agents exchange signed capability manifests without a central
registry.

It exists to explore what peer discovery *could* look like on top of the
Orcha runtime. It is not a live network, has no persistence, no reputation,
and no settlement — those are gated roadmap phases, not shipped features.

```bash
cd node && uv sync && uv run pytest
```
