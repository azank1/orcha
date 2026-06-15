import { useEffect, useState } from 'react'
import { useSessionStore } from '../../store/session'
import { credentials } from '../../api/client'
import type { AgentSecretItem } from '../../api/client'
import { Toggle } from '../ui/Toggle'
import { Button } from '../ui/Button'
import { cn } from '../ui/cn'


export function CredentialsModal() {
  const sessionId = useSessionStore((s) => s.sessionId)
  const sessionName = useSessionStore((s) => s.sessionName)
  const agents = useSessionStore((s) => s.agents)
  const isOpen = useSessionStore((s) => s.credentialsModalOpen)
  const close = useSessionStore((s) => s.closeCredentialsModal)

  const [secrets, setSecrets] = useState<AgentSecretItem[]>([])
  const [connectedMap, setConnectedMap] = useState<Record<string, boolean>>({})
  const [inputValues, setInputValues] = useState<Record<string, string>>({})
  const [permanent, setPermanent] = useState<Record<string, boolean>>({})
  const [saving, setSaving] = useState<Record<string, boolean>>({})
  const [loading, setLoading] = useState(false)

  const secretKey = (s: AgentSecretItem) => `${s.agent_id}:${s.var_name}`

  useEffect(() => {
    if (!isOpen || agents.length === 0) {
      setSecrets([])
      return
    }
    setLoading(true)
    const agentIds = agents.map((a) => a.agent_id)
    credentials
      .getRequired(agentIds)
      .then((items) => setSecrets(items))
      .catch(() => setSecrets([]))
      .finally(() => setLoading(false))
  }, [isOpen, agents])

  if (!isOpen) return null

  const requiredSecrets = secrets.filter((s) => s.required)
  const allConnected = requiredSecrets.every((s) => connectedMap[secretKey(s)])
  const connectedCount = secrets.filter((s) => connectedMap[secretKey(s)]).length

  const handleSave = async (secret: AgentSecretItem) => {
    const key = secretKey(secret)
    const value = inputValues[key]
    if (!value?.trim()) return
    setSaving((s) => ({ ...s, [key]: true }))
    try {
      await credentials.set({
        agent_id: secret.agent_id,
        var_name: secret.var_name,
        value: value.trim(),
        scope: permanent[key] ? 'permanent' : 'session',
        session_id: sessionId ?? undefined,
      })
      setConnectedMap((m) => ({ ...m, [key]: true }))
      setInputValues((v) => ({ ...v, [key]: '' }))
    } catch {
      // surface error in real impl
    } finally {
      setSaving((s) => ({ ...s, [key]: false }))
    }
  }

  const handleDelete = async (secret: AgentSecretItem) => {
    const key = secretKey(secret)
    try {
      await credentials.delete({
        agent_id: secret.agent_id,
        var_name: secret.var_name,
        scope: permanent[key] ? 'permanent' : 'session',
        session_id: sessionId ?? undefined,
      })
      setConnectedMap((m) => ({ ...m, [key]: false }))
    } catch { /* ignore */ }
  }

  const subtitle = sessionName ?? (sessionId ? `Session ${sessionId.slice(0, 8)}` : 'Active Session')

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-label="Credentials"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-surface-canvas/70"
        onClick={close}
        aria-hidden="true"
      />

      {/* Modal */}
      <div className="relative w-[480px] max-h-[90vh] flex flex-col bg-surface-elevated border border-surface-border rounded-lg shadow-lg overflow-hidden">
        {/* Header */}
        <div className="flex items-center gap-3 px-5 h-14 border-b border-surface-border shrink-0">
          <div className="size-9 flex items-center justify-center rounded-md bg-brand-primary-dim text-base">
            🔑
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[15px] font-semibold text-text-heading leading-none">Credentials</p>
            <p className="text-caption text-text-secondary mt-0.5">{subtitle}</p>
          </div>
          <button
            onClick={close}
            aria-label="Close credentials modal"
            className="text-lg text-text-secondary hover:text-text-body transition-colors"
          >
            ×
          </button>
        </div>

        <div className="overflow-y-auto scrollbar-thin flex-1 p-4 flex flex-col gap-3">
          {loading ? (
            <div className="flex items-center justify-center h-20 text-text-secondary text-label">
              Loading…
            </div>
          ) : secrets.length === 0 ? (
            <div className="flex items-center justify-center h-20 text-text-secondary text-label">
              No credentials required for this session.
            </div>
          ) : (
            <>
              {/* Status banner */}
              <div
                className={cn(
                  'flex items-center gap-2 h-10 px-3 rounded-md border',
                  allConnected
                    ? 'bg-semantic-successDim border-[#0A4A26]'
                    : 'bg-semantic-warningDim border-[#2D2000]',
                )}
              >
                <span
                  className={cn(
                    'size-2 rounded-full shrink-0',
                    allConnected ? 'bg-semantic-success' : 'bg-semantic-warning',
                  )}
                />
                <span
                  className={cn(
                    'text-label font-medium',
                    allConnected ? 'text-semantic-success' : 'text-semantic-warning',
                  )}
                >
                  {allConnected
                    ? `All required credentials connected (${connectedCount}/${secrets.length} total)`
                    : `${connectedCount}/${secrets.length} credentials connected`}
                </span>
              </div>

              {/* Credential rows */}
              {secrets.map((secret) => {
                const key = secretKey(secret)
                const connected = connectedMap[key] ?? false
                return (
                  <div
                    key={key}
                    className="rounded-md bg-surface-overlay border border-surface-border p-4"
                  >
                    {/* Top row */}
                    <div className="flex items-center gap-2">
                      <span className="text-label font-semibold text-text-heading flex-1 truncate">
                        {secret.var_name}
                      </span>
                      <span className="text-[10px] text-text-disabled truncate max-w-[120px]">
                        {secret.agent_name}
                      </span>
                      {secret.required && (
                        <span className="h-5 px-1.5 rounded-xs border border-surface-borderLight text-[10px] font-semibold text-text-secondary tracking-[0.8px] uppercase">
                          Required
                        </span>
                      )}
                      <div className="flex items-center gap-1.5 ml-auto shrink-0">
                        <span
                          className={cn(
                            'flex items-center justify-center h-7 px-2 rounded-sm border text-[11px] font-semibold',
                            connected
                              ? 'bg-semantic-successDim border-[#0A4A26] text-semantic-success'
                              : 'bg-semantic-errorDim border-[#3D1212] text-semantic-error',
                          )}
                        >
                          {connected ? '✓ Connected' : '✗ Missing'}
                        </span>
                        {connected && (
                          <button
                            onClick={() => handleDelete(secret)}
                            aria-label={`Remove ${secret.var_name}`}
                            className="text-surface-muted hover:text-semantic-error transition-colors text-sm"
                          >
                            🗑
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Description */}
                    {secret.description && (
                      <p className="mt-1.5 text-[11px] text-text-secondary">{secret.description}</p>
                    )}

                    {/* Input area (only if not connected) */}
                    {!connected && (
                      <div className="mt-3 flex flex-col gap-2">
                        <input
                          type="password"
                          value={inputValues[key] ?? ''}
                          onChange={(e) => setInputValues((v) => ({ ...v, [key]: e.target.value }))}
                          placeholder="Paste value…"
                          aria-label={`${secret.var_name} value`}
                          className="w-full h-10 px-3 rounded-md bg-surface-base border border-surface-borderLight text-label text-text-body placeholder:text-text-disabled focus:outline-none focus:border-brand-primary"
                        />
                        <div className="flex items-center justify-between">
                          <Toggle
                            checked={permanent[key] ?? false}
                            onChange={(v) => setPermanent((p) => ({ ...p, [key]: v }))}
                            label="Save permanently for all sessions"
                            id={`perm-${key}`}
                          />
                          <Button
                            size="sm"
                            onClick={() => handleSave(secret)}
                            loading={saving[key]}
                            disabled={!inputValues[key]?.trim()}
                          >
                            Save
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-4 border-t border-surface-border shrink-0">
          <Button className="w-full h-11" onClick={close}>
            Done
          </Button>
        </div>
      </div>
    </div>
  )
}
