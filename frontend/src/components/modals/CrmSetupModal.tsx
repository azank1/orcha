/**
 * CrmSetupModal — standalone CRM connection modal (opened via store.openCrmModal).
 *
 * Two-step flow:
 *   Step 1 — pick a CRM from a 2×2 grid (no expansion needed)
 *   Step 2 — connection panel appears below the grid for the selected CRM
 *
 * OAuth CRMs: opens a popup, polls for close, then activates.
 * HubSpot:    PAT token input with instructions.
 */
import { useEffect, useRef, useState } from 'react'
import { leadGenBaseUrl } from '../../lib/leadGenBaseUrl'
import { useSessionStore } from '../../store/session'
import { Button } from '../ui/Button'
import { cn } from '../ui/cn'

type CrmType = 'hubspot' | 'gsheets' | 'excel' | 'notion'

interface CrmOption {
  id: CrmType
  label: string
  icon: string
  authMethod: 'pat' | 'oauth'
  oauthProvider?: string
  description: string
  hint: string
}

const CRM_OPTIONS: CrmOption[] = [
  {
    id: 'gsheets',
    label: 'Google Sheets',
    icon: '🟢',
    authMethod: 'oauth',
    oauthProvider: 'gsheets',
    description: 'Spreadsheet',
    hint: 'Authorize with your Google account — a new sheet is created automatically.',
  },
  {
    id: 'hubspot',
    label: 'HubSpot',
    icon: '🟠',
    authMethod: 'pat',
    description: 'CRM',
    hint: 'Paste your Private App Token from HubSpot → Settings → Integrations → Private Apps.',
  },
  {
    id: 'notion',
    label: 'Notion',
    icon: '⬛',
    authMethod: 'oauth',
    oauthProvider: 'notion',
    description: 'Database',
    hint: 'Authorize with your Notion account to write leads to a database.',
  },
  {
    id: 'excel',
    label: 'Excel (OneDrive)',
    icon: '🔵',
    authMethod: 'oauth',
    oauthProvider: 'excel',
    description: 'Spreadsheet',
    hint: 'Authorize with your Microsoft account — a workbook is created in OneDrive.',
  },
]

export function CrmSetupModal() {
  const store = useSessionStore()
  const sessionId = store.sessionId
  const isOpen = store.crmModalOpen
  const leadGenUrl = leadGenBaseUrl()

  const [activeCrm, setActiveCrm]      = useState<CrmType | null>(null)
  const [selected, setSelected]        = useState<CrmType | null>('gsheets')
  const [patToken, setPatToken]        = useState('')
  const [connecting, setConnecting]    = useState(false)
  const [connected, setConnected]      = useState<CrmType | null>(null)
  const [error, setError]              = useState<string | null>(null)
  const popupRef = useRef<Window | null>(null)
  const pollRef  = useRef<ReturnType<typeof setInterval> | null>(null)

  // Load current CRM status when modal opens
  useEffect(() => {
    if (!isOpen || !sessionId) return
    setError(null)
    setConnected(null)
    setSelected(null)
    setPatToken('')
    fetch(`${leadGenUrl}/crm/status?tenant_id=${encodeURIComponent(sessionId)}`)
      .then((r) => r.json())
      .then((data) => {
        const crm = data.crm_type ?? null
        setActiveCrm(crm)
        if (crm) setSelected(crm)
      })
      .catch(() => setError('Could not load CRM status'))
  }, [isOpen, sessionId, leadGenUrl])

  // Clean up popup poll when modal closes
  useEffect(() => {
    if (!isOpen) {
      if (pollRef.current) clearInterval(pollRef.current)
      popupRef.current?.close()
    }
  }, [isOpen])

  if (!isOpen) return null

  const selectCrm = (id: CrmType) => {
    if (connected) return
    setSelected(id)
    setError(null)
    setPatToken('')
  }

  const connectPat = async () => {
    if (!sessionId || !patToken.trim() || !selected) return
    setConnecting(true)
    setError(null)
    try {
      const res = await fetch(`${leadGenUrl}/crm/hubspot/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tenant_id: sessionId, token: patToken.trim() }),
      })
      if (!res.ok) throw new Error(`Server error ${res.status}`)
      await fetch(`${leadGenUrl}/crm/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tenant_id: sessionId, crm_type: selected }),
      })
      setConnected(selected)
      setActiveCrm(selected)
      setPatToken('')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to connect')
    } finally {
      setConnecting(false)
    }
  }

  const connectOAuth = async (opt: CrmOption) => {
    if (!sessionId || !opt.oauthProvider) return
    setConnecting(true)
    setError(null)
    try {
      const res = await fetch(
        `${leadGenUrl}/oauth/${opt.oauthProvider}/connect?tenant_id=${encodeURIComponent(sessionId)}`,
      )
      if (!res.ok) throw new Error(`Could not get auth URL (${res.status})`)
      const data = await res.json()
      if (!data.auth_url) throw new Error('No auth_url returned')

      const popup = window.open(data.auth_url, 'crm_oauth', 'width=600,height=720,left=200,top=100')
      if (!popup) {
        setError('Popup blocked — allow popups for this site and try again.')
        setConnecting(false)
        return
      }
      popupRef.current = popup

      pollRef.current = setInterval(async () => {
        if (!popup.closed) return
        if (pollRef.current) clearInterval(pollRef.current)
        try {
          await fetch(`${leadGenUrl}/crm/select`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tenant_id: sessionId, crm_type: opt.id }),
          })
          setConnected(opt.id)
          setActiveCrm(opt.id)
        } catch {
          setError(`Authorized but could not activate ${opt.label} — try again.`)
        } finally {
          setConnecting(false)
        }
      }, 600)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'OAuth failed')
      setConnecting(false)
    }
  }

  const selectedOpt  = CRM_OPTIONS.find((o) => o.id === selected)
  const connectedOpt = CRM_OPTIONS.find((o) => o.id === connected)
  const activeOpt    = CRM_OPTIONS.find((o) => o.id === activeCrm)

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-label="Connect CRM"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-surface-canvas/70"
        onClick={() => store.closeCrmModal()}
        aria-hidden="true"
      />

      <div className="relative flex flex-col bg-surface-elevated border border-surface-border rounded-xl shadow-2xl overflow-hidden w-[560px] max-h-[88vh]">
        {/* Header */}
        <div className="flex items-center gap-3 px-5 h-[60px] border-b border-surface-border shrink-0 bg-surface-base">
          <div className="size-9 flex items-center justify-center rounded-lg bg-brand-primary-dim border border-[rgba(59,110,248,0.2)] text-base shrink-0">
            🗃
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[14px] font-semibold text-text-heading leading-snug">Connect CRM</p>
            <p className="text-[11px] text-text-secondary mt-px">
              {activeOpt ? `Currently: ${activeOpt.label}` : 'Qualified leads will be saved here'}
            </p>
          </div>
          <button
            onClick={() => store.closeCrmModal()}
            className="text-text-disabled hover:text-text-secondary text-xl leading-none ml-2"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto scrollbar-thin px-5 py-4 flex flex-col gap-4">

          {/* Step 1 — CRM picker grid */}
          <div>
            <p className="text-[11px] font-semibold text-text-secondary uppercase tracking-wide mb-2">
              Step 1 — Choose a destination
            </p>
            <div className="grid grid-cols-2 gap-2">
              {CRM_OPTIONS.map((opt) => {
                const isActive    = activeCrm === opt.id
                const isConnected = connected === opt.id
                const isSelected  = selected === opt.id
                const done        = isActive || isConnected
                return (
                  <button
                    key={opt.id}
                    type="button"
                    disabled={!!(connected && !isConnected)}
                    onClick={() => selectCrm(opt.id)}
                    className={cn(
                      'flex items-center gap-2.5 px-3 py-2.5 rounded-lg border text-left transition-colors',
                      done
                        ? 'border-semantic-success bg-semantic-successDim cursor-default'
                        : isSelected
                          ? 'border-brand-primary bg-brand-primary/5'
                          : 'border-surface-border bg-surface-base hover:border-surface-muted',
                    )}
                  >
                    <span className="text-base shrink-0">{opt.icon}</span>
                    <div className="min-w-0">
                      <p className={cn('text-[13px] font-medium leading-snug', done ? 'text-semantic-success' : 'text-text-heading')}>
                        {opt.label}
                      </p>
                      <p className="text-[10px] text-text-secondary">{opt.description}</p>
                    </div>
                    {done && (
                      <span className="ml-auto text-[10px] font-bold text-semantic-success shrink-0">✓</span>
                    )}
                    {isSelected && !done && (
                      <span className="ml-auto size-2.5 rounded-full bg-brand-primary shrink-0" />
                    )}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Step 2 — connection panel */}
          {selectedOpt && !connected && activeCrm !== selected && (
            <div className="rounded-lg border border-surface-border bg-surface-base px-4 py-3 flex flex-col gap-2.5">
              <p className="text-[11px] font-semibold text-text-secondary uppercase tracking-wide">
                Step 2 — Connect {selectedOpt.label}
              </p>
              <p className="text-[12px] text-text-secondary leading-relaxed">{selectedOpt.hint}</p>

              {selectedOpt.authMethod === 'pat' ? (
                <div className="flex flex-col gap-2">
                  <input
                    type="password"
                    value={patToken}
                    onChange={(e) => setPatToken(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && connectPat()}
                    placeholder="pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                    autoFocus
                    className="h-9 px-3 rounded-md bg-surface-canvas border border-surface-borderLight text-[12px] text-text-body placeholder:text-text-disabled focus:outline-none focus:border-brand-primary font-mono"
                  />
                  <Button
                    size="sm"
                    onClick={connectPat}
                    loading={connecting}
                    disabled={!patToken.trim()}
                    className="self-start bg-brand-primary hover:bg-brand-primary-hover text-white border-0"
                  >
                    Connect HubSpot
                  </Button>
                </div>
              ) : (
                <Button
                  size="sm"
                  onClick={() => connectOAuth(selectedOpt)}
                  loading={connecting}
                  className="self-start bg-brand-primary hover:bg-brand-primary-hover text-white border-0"
                >
                  {connecting ? `Waiting for ${selectedOpt.label}…` : `Authorize ${selectedOpt.label}`}
                </Button>
              )}
            </div>
          )}

          {/* Already active — show re-connect option */}
          {selectedOpt && activeCrm === selected && !connected && (
            <div className="rounded-lg border border-semantic-success bg-semantic-successDim px-4 py-3 flex flex-col gap-2">
              <p className="text-[13px] text-semantic-success font-medium">
                ✓ {selectedOpt.label} is your active CRM
              </p>
              <p className="text-[11px] text-text-secondary">
                Leads from the lead-gen agent will be saved here automatically.
              </p>
              {selectedOpt.authMethod === 'oauth' && (
                <Button
                  size="sm"
                  onClick={() => connectOAuth(selectedOpt)}
                  loading={connecting}
                  className="self-start bg-surface-overlay border border-surface-borderLight text-text-body hover:border-surface-muted"
                >
                  Re-authorize {selectedOpt.label}
                </Button>
              )}
            </div>
          )}

          {/* Success banner after fresh connect */}
          {connectedOpt && (
            <div className="flex items-center gap-2 px-3 py-2.5 rounded-lg bg-semantic-successDim border border-[rgba(34,197,94,0.3)] text-[13px] text-semantic-success">
              <span className="text-base">{connectedOpt.icon}</span>
              <span><span className="font-semibold">{connectedOpt.label}</span> connected successfully.</span>
            </div>
          )}

          {error && (
            <p className="text-[12px] text-semantic-error px-3 py-2 rounded-md bg-semantic-errorDim border border-[rgba(239,68,68,0.25)]">
              {error}
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end px-5 py-4 border-t border-surface-border shrink-0 bg-surface-base">
          <Button
            size="sm"
            onClick={() => store.closeCrmModal()}
            className="bg-surface-overlay border border-surface-borderLight text-text-body hover:border-surface-muted"
          >
            Done
          </Button>
        </div>
      </div>
    </div>
  )
}
