# CanvasKit on Puter (PoC)

A standalone viewer that renders an Orcha **CanvasKit `UIManifest`** as a
persistent app on [Puter](https://puter.com) — an open-source "internet OS".

> **The thesis:** your agent's output isn't a chat reply that evaporates — it's a
> persistent dashboard app that's just *there* in an OS, updating when the agent
> re-runs. This is Orcha's DAPN Plane 3 (persistent runtime) + Plane 4 (consumer
> surface) validated on a real host, with zero infra to build.

## What this is

The 8 CanvasKit components + `CanvasRenderer` are lifted verbatim from
`frontend/src/components/canvas/` (they're pure `(spec) → JSX`, no store/SSE/API
coupling). This app feeds them a manifest read from the user's Puter storage,
falling back to a bundled sample when run outside Puter.

```
Orcha run ──▶ UIManifest (JSON) ──▶ (written to Puter FS) ──▶ this app renders it
```

## Run locally (no Puter account needed)

```bash
cd apps/canvaskit-puter
npm install
npm run dev      # opens with the bundled sample manifest
npm run build    # typecheck + production bundle → dist/
```

Opened outside Puter, `window.puter` is absent and the app renders
`src/sample-manifest.ts`. All Puter calls are isolated in `src/puter.ts` and
degrade gracefully.

## Publish to Puter (needs a Puter account)

1. Sign in at [puter.com](https://puter.com) (or your self-hosted Puter instance).
2. Build: `npm run build` → static bundle in `dist/`.
3. Deploy the `dist/` folder as a Puter app — either:
   - the **Puter Developer Center** → *Create App* → upload `dist/`, or
   - the Puter CLI / hosting API (`puter.hosting`) to publish `dist/` to a subdomain.
4. Open the app in Puter. On first load it prompts Puter sign-in, then reads the
   manifest from `~/orcha/latest-dashboard.json` (override via
   `VITE_MANIFEST_PATH`). Use **Save sample to Puter** in the header to seed one.
5. **Feed a real Orcha manifest (PoC):** export the `canvas_manifest` payload
   from an Orcha run to JSON and write it to `~/orcha/latest-dashboard.json` in
   your Puter Files, then hit **Refresh**. (The automated Orcha→Puter write via
   `writeManifest()` in a post-run hook is the v2.)

## ⚠ AGPL boundary — do not cross

Puter **core** is AGPL-3.0 (viral over the network). This PoC stays safe by
**integrating, not forking**:

- This app is **Apache-2.0** and **independent** — it is not a fork, derivative,
  or modification of Puter core.
- It uses **`puter.js`** (the CDN client SDK in `index.html`) purely as a client
  library at runtime — the same way any app calls an API. All SDK access is
  isolated in `src/puter.ts`.
- The Orcha **closed moat** (FulfillmentRecorder, semantic judge, GNN ranker)
  **never touches Puter** — it stays a remote service Orcha calls server-side.
  Puter only ever sees an already-rendered, already-open `UIManifest`.

**Rules:** integrate, don't fork · call the moat, don't merge it · never bundle
or derive from AGPL Puter core.

**Pre-publish check:** confirm `puter.js`'s own license is permissive
(MIT/Apache — it's a separate package from the AGPL core). It's loaded via CDN
`<script>` so it is never bundled into this app regardless.
