# Metis Owl Lab

Playground for the locked Metis owl mascot. **Canonical source:** `frontend/src/components/ui/metis/`.

## Run

From `frontend/`:

```bash
npm run dev:owl
```

Opens **http://localhost:3100/** — imports `@metis` from the main app (single source of truth).

## Integrate in product UI

```tsx
import { OwlMascot, mapSessionToOwlState } from '@/components/ui/metis'

<OwlMascot state={mapSessionToOwlState(sessionStatus)} size={64} />
```

See `src/components/ui/metis/README.md` for states, theming, and file map.
