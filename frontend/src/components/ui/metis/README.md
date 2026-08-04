# Metis (owl mascot) — locked design

Canonical SVG component for **Metis**, Orcha's owl mascot. Approved in owl-lab; use this module for all product UI.

## Usage

```tsx
import { OwlMascot, mapSessionToOwlState } from '@/components/ui/metis'
// or
import { OwlMascot } from '@/components/ui/OwlMascot'

<OwlMascot state={mapSessionToOwlState(sessionStatus)} size={64} />
```

## States

| `OwlState`   | Eye ring   | Motion                          |
|--------------|------------|---------------------------------|
| `idle`       | black      | bob, gentle wing flap           |
| `executing`  | yellow     | lean, locked stare              |
| `verified`   | green      | hops, wing flaps                |
| `error`      | red        | shake, wings raised             |

Session mapping: `idle` → idle · `running`/`interrupted` → executing · `complete` → verified · `failed` → error.

## Files

- `OwlMascot.tsx` — React SVG composer
- `owlPaths.ts` / `owlEyes.ts` / `owlEars.ts` / `owlWings.ts` / `owlFrown.ts` — geometry
- `OwlEarLeft.tsx` / `OwlEarRight.tsx` — solid ear tufts
- `owl-mascot.css` — animations (imported by component)
- `mapSessionToOwlState.ts` — session → state helper

ViewBox: **100×100**. Default render size: **64px** (scale freely).

## Playground

`npm run dev:owl` from `frontend/` — isolated lab imports this module via `@metis` alias.

## Theming

Override `--owl-*` CSS variables in `:root` (see `frontend/src/index.css`). Do not edit path geometry for seasonal reskins unless intentionally revising the mascot.
