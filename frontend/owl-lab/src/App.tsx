import { useState } from 'react'

import { OwlMascot, type OwlState } from '@metis'

const STATES: readonly { id: OwlState; label: string; dot: string }[] = [
  { id: 'idle', label: 'idle', dot: '#1a1a1a' },
  { id: 'executing', label: 'executing', dot: '#f59e0b' },
  { id: 'verified', label: 'verified', dot: '#22c55e' },
  { id: 'error', label: 'error', dot: '#ef4444' },
]

/** Maps Orcha's real SessionStatus (frontend/src/types/index.ts) onto OwlState. */
const SESSION_MAPPING: readonly { session: string; owl: string }[] = [
  { session: 'idle', owl: 'idle' },
  { session: 'running / interrupted', owl: 'executing' },
  { session: 'complete', owl: 'verified' },
  { session: 'failed', owl: 'error' },
]

export function App() {
  const [state, setState] = useState<OwlState>('idle')
  const [showPerch, setShowPerch] = useState(true)
  const [size, setSize] = useState(220)

  return (
    <div className="lab">
      <header className="lab-header">
        <h1>Metis Owl Lab</h1>
        <p>Isolated playground — no auth, no router, no main app deps.</p>
      </header>

      <div className="lab-stage">
        <OwlMascot state={state} size={size} showPerch={showPerch} />
      </div>

      <div className="lab-controls">
        {STATES.map((s) => (
          <button
            key={s.id}
            type="button"
            className={s.id === state ? 'lab-btn lab-btn--active' : 'lab-btn'}
            onClick={() => setState(s.id)}
          >
            <span className="lab-btn-dot" style={{ background: s.dot }} />
            {s.label}
          </button>
        ))}
      </div>

      <ul className="lab-legend">
        {SESSION_MAPPING.map((m) => (
          <li key={m.session}>
            <code>{m.session}</code> → {m.owl}
          </li>
        ))}
      </ul>

      <div className="lab-sliders">
        <label>
          <input
            type="checkbox"
            checked={showPerch}
            onChange={(e) => setShowPerch(e.target.checked)}
          />
          perch
        </label>
        <label>
          size
          <input
            type="range"
            min={64}
            max={320}
            value={size}
            onChange={(e) => setSize(Number(e.target.value))}
          />
          {size}px
        </label>
      </div>

      <footer className="lab-footer">
        Black idle stare · yellow locked focus · green hop celebration · red
        alarm. Run with <code>npm run dev:owl</code> from <code>frontend/</code>.
      </footer>
    </div>
  )
}
