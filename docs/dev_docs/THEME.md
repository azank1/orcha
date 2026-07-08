# Theme — Cyber-Technical / Pro-Developer

Source of truth for the frontend visual system. Read this before adding a new
component or touching colors/typography.

## Token layers (edit in lockstep)

Two files must always agree — they define the same palette twice for two
different consumers:

- [frontend/tailwind.config.ts](../../frontend/tailwind.config.ts) — `theme.extend.colors` — used by every Tailwind utility class (`bg-surface-elevated`, `text-text-secondary`, etc).
- [frontend/src/index.css](../../frontend/src/index.css) `:root` — CSS custom properties (`--color-surface-elevated`, etc) — used by anything reading raw CSS vars (the Metis owl mascot, a few inline styles).

If you change a color, change it in **both** files with the same hex. A
mismatch is invisible in one and wrong in the other.

Recharts is the one exception: SVG chart libraries need literal color
strings, not Tailwind classes. Those live in
[frontend/src/components/canvas/chartTokens.ts](../../frontend/src/components/canvas/chartTokens.ts) —
update that file too when the palette changes, and never re-inline a hex
directly inside a chart component.

## Rule: no hardcoded hex in components

Every color a component uses should resolve to a token
(`bg-surface-elevated`, `text-semantic-error`, `border-surface-border`, …),
not a literal `#1E2330` or `rgba(30,35,48,...)`. A hardcoded hex silently
drifts out of sync the next time the palette is re-based — this happened
once already (`LineChart`/`PieChart` tooltips and default series colors),
which is why `chartTokens.ts` exists.

Exceptions that are fine to hardcode:
- `frontend/src/components/ui/Logo.tsx` and `logo.svg` — the brand mark is a
  fixed asset, not a themed surface.
- One-off `rgba(59,110,248,0.3)`-style translucent brand borders (e.g. the
  logo badge glow) — these are intentional opacity variants of
  `brand.primary`'s literal RGB, not surface/text tokens, and Tailwind's
  color-with-opacity syntax doesn't apply cleanly to config-defined hex
  colors here.

## Rule: monospace for data, sans for prose

`font-mono` (JetBrains Mono, loaded via `@fontsource/jetbrains-mono` in
`index.css`) is for anything that reads as **data**: metric values, table
numeric/currency/percent cells, chart axis ticks/tooltips, cost figures,
IDs, timestamps, code blocks, and tool-call JSON. `font-sans` (Inter, the
default) is for everything else — headings, body copy, labels, buttons.

When in doubt: if a human would want it to line up in a fixed-width column,
it's mono.

## fontSize scale

Defined in `tailwind.config.ts` under `theme.extend.fontSize`:
`display`, `h1`, `h2`, `h3`, `body-lg`, `body-md`, `label`, `caption`,
`mono`. Each bundles a font-size + line-height (+ font-weight where
relevant) — prefer these over an arbitrary `text-[13px]` when the target
size, line-height, *and* weight all match one of the named sizes exactly.
Don't force a mapping that changes the visual weight just to avoid an
arbitrary value — an arbitrary `text-[30px]` is fine when nothing in the
scale actually matches.

## Density

Canvas/table surfaces should stay tight — the spec's high-density band is
4-8px vertical padding on data rows (see `DataTable.tsx`'s `py-1.5` body
cells). UI chrome (nav, buttons, cards) can stay at normal Tailwind spacing;
density applies to *data-dense* surfaces specifically, not the whole app.

## Brand glow

`shadow-blue` / `shadow-cyan` (defined alongside the color tokens) are the
"Metis-blue AI presence" accent — reserved for: the active nav/sidebar item,
the homepage logo badge, and the primary CTA on the home screen. Don't apply
it to every button; it's an accent for a small number of "this is where the
AI lives" moments, not a default button state.

## Checklist for new components

- [ ] All colors are token classes (`bg-surface-*`, `text-text-*`,
      `border-surface-*`, `text-semantic-*`, `bg-brand-*`) — no literal hex.
- [ ] Numeric/data content uses `font-mono`; prose uses the default sans.
- [ ] If it's a recharts component, pull colors/fonts from `chartTokens.ts`.
- [ ] If it needs a genuinely new color, add it to `tailwind.config.ts`
      **and** `index.css` `:root` in the same change, not just one.
