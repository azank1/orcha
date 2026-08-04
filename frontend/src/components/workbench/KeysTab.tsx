import { useState } from 'react'
import { credentials } from '../../api/client'
import { useByokStore } from '../../store/byok'
import { useSessionStore } from '../../store/session'

function maskKey(key: string): string {
  if (!key) return '—'
  const tail = key.length > 4 ? key.slice(-4) : ''
  return tail ? `••••••••${tail}` : '••••••••'
}

/** BYOK console: current model-key state, reopen setup, clear key. */
export function KeysTab() {
  const mode = useByokStore((s) => s.mode)
  const baseUrl = useByokStore((s) => s.baseUrl)
  const apiKey = useByokStore((s) => s.apiKey)
  const model = useByokStore((s) => s.model)
  const openOnboarding = useByokStore((s) => s.openOnboarding)
  const clearConfig = useByokStore((s) => s.clearConfig)

  const sessionId = useSessionStore((s) => s.sessionId)
  const byokSessionId = useSessionStore((s) => s.byokSessionId)
  const applied = Boolean(sessionId && byokSessionId === sessionId)

  const [clearing, setClearing] = useState(false)

  const handleClear = async () => {
    setClearing(true)
    try {
      if (sessionId) {
        // Best-effort: remove the session-scoped '__llm__' creds server-side.
        for (const var_name of ['base_url', 'api_key', 'model'] as const) {
          await credentials
            .delete({ agent_id: '__llm__', var_name, scope: 'session', session_id: sessionId })
            .catch(() => {})
        }
      }
    } finally {
      clearConfig()
      setClearing(false)
    }
  }

  return (
    <div className="px-3">
      <p className="px-1 mb-2 text-[10px] font-semibold text-text-disabled tracking-caps uppercase">
        BYOK Console
      </p>

      <div className="rounded-md border border-surface-border bg-surface-overlay px-3 py-2.5 flex flex-col gap-1.5">
        <Row label="mode" value={mode === 'byok' ? 'byok' : 'hosted'} />
        {mode === 'byok' && (
          <>
            <Row label="model" value={model || '—'} />
            <Row label="base_url" value={baseUrl || '—'} />
            <Row label="api_key" value={maskKey(apiKey)} />
            <Row
              label="session"
              value={applied ? 'applied' : 'not applied'}
              valueClass={applied ? 'text-semantic-success' : 'text-text-disabled'}
            />
          </>
        )}
      </div>

      <div className="mt-2 flex items-center gap-2">
        <button
          onClick={openOnboarding}
          className="h-7 px-2.5 rounded-sm border border-surface-borderLight bg-surface-overlay font-mono text-[10px] text-text-body hover:border-surface-muted transition-colors"
        >
          {mode === 'byok' ? 'edit key' : 'set up key'}
        </button>
        {mode === 'byok' && (
          <button
            onClick={handleClear}
            disabled={clearing}
            className="h-7 px-2.5 rounded-sm border border-surface-borderLight bg-surface-overlay font-mono text-[10px] text-semantic-error hover:border-semantic-error/50 disabled:opacity-50 transition-colors"
          >
            {clearing ? 'clearing…' : 'clear key'}
          </button>
        )}
      </div>

      <p className="mt-2 px-1 font-mono text-[10px] text-text-disabled">
        session-scoped — the key lives in the credentials vault, never in logs.
      </p>
    </div>
  )
}

function Row({
  label,
  value,
  valueClass,
}: {
  label: string
  value: string
  valueClass?: string
}) {
  return (
    <div className="flex items-baseline gap-2">
      <span className="w-16 shrink-0 font-mono text-[10px] text-text-disabled">{label}</span>
      <span className={`min-w-0 flex-1 truncate font-mono text-[11px] ${valueClass ?? 'text-text-body'}`}>
        {value}
      </span>
    </div>
  )
}
