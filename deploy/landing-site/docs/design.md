# Orcha Landing — Design System

Monochrome "observatory" design for metaorcha.ai. Adapted from the *6 Ascii Moon*
template (see `kimi files/` in orcha-internal) and reimplemented in our stack:
React 19 + Vite + Tailwind v4 + `motion` (no GSAP).

The site is a single monochrome theme — no light/dark toggle. Contrast comes
from alternating **bands** (black / paper), not from an accent color. There is
no accent color. Interactive states are expressed with opacity, borders and
motion only.

---

## 1. Tokens

Defined in `src/index.css` as CSS custom properties. Components must reference
tokens (`var(--bg)` etc.), never raw hex values, except inside `index.css`.

| Token | Value | Use |
|---|---|---|
| `--bg` | `#000000` | Dark band background |
| `--fg` | `#ffffff` | Text on dark bands |
| `--paper` | `#fafafa` | Light band background |
| `--ink` | `#0a0a0a` | Text on light bands |
| `--line-dark` | `#1f1f1f` | Hairlines/borders on dark bands |
| `--line-light` | `#0a0a0a` | Hairlines/borders on light bands (used at low opacity via `border-current`/opacity) |
| `--muted-dark` | `#a3a3a3` | Secondary text on dark |
| `--muted-light` | `#525252` | Secondary text on light |
| `--faint` | `#525252` | Tertiary text on dark |
| `--ok` | `#3ecf8e` | **Only** for verified/verdict semantics inside terminals and audit data — never decorative |

Legacy `--accent` (indigo) is removed. Status dots are white with a pulse
animation; the only hue allowed anywhere is `--ok` green in data contexts
(verdicts, "verified" labels inside run artifacts).

### Grain

A fixed full-viewport SVG-noise overlay (`.grain-overlay`, `z-index 50`,
`pointer-events none`, `opacity 0.10`, `mix-blend-mode overlay`) sits above
everything. It is part of the brand texture — keep it subtle; never above 0.12.

---

## 2. Typography

| Role | Font | Source |
|---|---|---|
| Display titles (hero, section titles) | **Geist Pixel** | `geist` npm package, woff2 via `@font-face` |
| UI + body (everything) | **IBM Plex Mono** | `@fontsource/ibm-plex-mono` |
| ASCII field / generative tiles | **Fragment Mono** | `@fontsource/fragment-mono` |

- `body` is IBM Plex Mono 15–16px / 1.6.
- Display titles: Geist Pixel, `clamp(2.5rem, 6vw, 4.5rem)`, tight leading
  (1.02–1.08), uppercase where the band label style applies.
- Band labels ("Protocol Architecture — Bridges 01–04" etc.): IBM Plex Mono,
  11–12px, uppercase, letter-spacing 0.12em, muted color.
- Inter / Space Grotesk / JetBrains Mono are gone. Do not reintroduce.

---

## 3. Band System (home page order)

| # | Band | Component | Notes |
|---|---|---|---|
| 1 | black | `SplitHero` | 40/60 split, ASCII moon right |
| 2 | paper | `Manifesto` | video/text split |
| 3 | black (thin) | `PipelineStrip` | 5-step execution flow |
| 4 | paper | `PluginDirectory` | 5 flip cards (4 plugins + contribute) → `/plugins/:slug` |
| 5 | paper | `ValuePropGrid` | re-skinned |
| 6 | black | `ObservationSection` | replay terminal + live dot + dock CTA |
| 7 | black | `InteractiveDAGArchitecture` | re-skinned |
| 8 | black | `ProtocolRing` | draggable 3D ring: protocol tiles + live sandbox fleet |
| 9 | paper | `SDKAndManifest` | re-skinned |
| 11 | black | `Footer` | lockup + status + ASCII backdrop |

Plus `SandboxDock` — floating pill → expandable window, mounted site-wide,
state survives route changes.

Routes `/docs`, `/roadmap`, `/contributing`, `/plugins/:slug` are separate
pages (react-router). `/bridges/:slug` redirects to `/plugins/:slug`.
Docs uses the paper band style (article-like).

---

## 4. Component Catalog & Reuse Map

### New components

- **`AsciiMoonField.tsx`** — canvas-rendered rotating ASCII sphere, mouse-
  reactive (rotation follows pointer), Fragment Mono, monochrome. Props:
  `glyphs` (charset), `speed`, `density`, `className`. Honors
  `prefers-reduced-motion` (renders one static frame). Used in:
  - `SplitHero` right panel (primary, full size)
  - `Footer` backdrop (small, slow, low opacity)
- **`ProtocolLogo.tsx`** — monochrome protocol marks (MCP, A2A, LangGraph
  from `src/assets/protocols/*.svg?raw`, currentColor; text tokens for
  A2UI/OpenAPI/gRPC; inline glyph paths for Computer-Use/CanvasKit).
- **`PluginCard.tsx`** — flip card (CSS 3D, hover on desktop, tap on touch).
  Front: logo + name. Back: real demo capture (`src/assets/proof/plugin-*.mp4`)
  + link to detail page. `ContributeCard` is the 5th card — same container,
  dashed border, links to docs + contributing.
- **`SplitHero.tsx`** — 40/60 editorial + moon field. Content from
  `src/data/siteConfig.ts` (`hero`). Includes quickstart copy-chips and CTAs.
- **`Manifesto.tsx`** — 16:9 video left (`src/assets/proof/card1-run.mp4`,
  autoplay/muted/loop/playsInline), editorial paragraph right.
- **`PipelineStrip.tsx`** — the 5-step execution flow (Goal → Gate →
  SuperAgent → Dispatch → CanvasKit).
- **`PluginDirectory.tsx`** — the 5-card plugins grid.
- **`PluginDetailPage.tsx`** — `/plugins/:slug`. Back link, demo clip panel,
  meta rows (handler path, stack), article paragraphs, CTA to the handler
  source on GitHub. The `canvaskit` slug additionally mounts
  `CanvasKitShowcase` below the article.
- **`ObservationSection.tsx`** — sandbox band: band label, quiet live dot
  (poller from `SANDBOX_STATUS_URL`), `RunReplayTerminal`, CTA that opens
  the dock via the `orcha:open-sandbox` window event.
- **`SandboxDock.tsx`** — floating "Run a goal" pill → expandable window
  with the sandbox iframe. Minimize/close, Esc closes, persists across
  routes. Listens for `orcha:open-sandbox`.
- **`ProtocolRing.tsx`** — draggable 3D ring of protocol tiles plus the live
  sandbox fleet (fetched from `sandbox/fleet`, 5 min refresh; protocols-only
  when the sandbox is unreachable). Drag hint fades after first drag; slow
  idle spin; static under `prefers-reduced-motion`.
- **`RunReplayTerminal.tsx`** — the real-run typing replay (data in
  `src/data/realRunReplay.ts`).

### Reused (re-skin only, no behavior change)

`ValuePropGrid`, `InteractiveDAGArchitecture`, `SDKAndManifest`,
`CanvasKitShowcase`, `RoadmapAndNonGoals`, `ContributionSection`,
`DocumentationPage`, `ScrollReveal`, `Navbar`, `Footer`.

### Deleted / superseded

`HeroSection`, `HeroShaderCanvas`, `ProtocolSlideshow`, `ProofCards`,
`VerifiedRunsSection`, `GoalDecomposition`, `ProtocolIcons`,
`BridgeDirectory`, `ArchiveCarousel` (evidence vault — dropped; the
protocol ring takes its slot).

---

## 5. Motion

- Library: `motion` only. Easing standard: `cubic-bezier(0.22, 1, 0.36, 1)`,
  duration 0.5–0.6s for reveals.
- `ScrollReveal` wraps every band (direction `up`, small delays).
- CTA micro-interaction: text-roll hover (duplicated label in an
  `overflow-hidden` column, `group-hover:-translate-y-1/2`, 500ms) + arrow
  circle rotating −45°. Used on primary CTAs site-wide.
- ASCII moon: continuous slow rotation, pointer-reactive; static frame under
  `prefers-reduced-motion`.
- Archive carousel: inertial rotation, preview overlay scale/fade 300ms.

---

## 6. Content & Assets

- All copy lives in `src/data/siteConfig.ts` (ported from the zip's
  `config.ts`, GitHub URLs pointed at `solvent-metaorcha/orcha`).
- Brand: `public/brand/` (glyph-bare.svg, icon-tile.svg, lockup-dark.svg,
  lockup-light.svg) from the zip; favicon = orcha-icon-128.png.
- Diagrams: `public/diagrams/` (islands, missing-layer, timeline,
  verifier-bottleneck SVGs from the zip's article-assets).
- Proof artifacts stay in `src/assets/proof/`.
- **Rule:** every visual artifact must be real (captured run, real diagram,
  generated ASCII). No stock imagery, no decorative illustration.

## 7. Rules for Future Development

1. No accent colors. If you reach for a hue, use opacity or `--ok` (data only).
2. Tokens over hex. New values go in `index.css` first.
3. Bands alternate; a new section picks the band that continues the rhythm.
4. Geist Pixel is for titles only; IBM Plex Mono everywhere else.
5. Mono space is the UI voice — keep copy terse, factual, no marketing slop.
6. Every animation must have a `prefers-reduced-motion` path.
7. Naming: the SDK is "Orcha SDK" in all visible copy ("emerge" appears only
   in literal commands/file names). No `PAYMENT_MODE`/infra internals on
   landing or footer. No vanity counters (runs-today chips, fake metrics).
8. Every visual artifact must be real (captured run, real diagram) — no
   staged demos. Plugin card backs play captures from the live sandbox.
