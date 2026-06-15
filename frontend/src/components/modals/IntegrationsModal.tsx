/**
 * IntegrationsModal — unified hub for all agent integrations.
 *
 * Sections:
 *   • CRM & Spreadsheets  — live OAuth / PAT (HubSpot, Google Sheets, Notion, Excel)
 *   • Email               — Gmail OAuth (already implemented in lead-gen agent)
 *   • Messaging           — Coming Soon (WhatsApp, Telegram, Slack)
 *   • E-commerce          — Coming Soon (Shopify, Stripe, WooCommerce)
 *   • Social Media        — Coming Soon (LinkedIn, X, Instagram)
 *
 * Status for all live integrations is fetched from the lead-gen agent's
 * /tool-settings/status endpoint in a single call.
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import { useSessionStore } from '../../store/session'
import { Button } from '../ui/Button'
import { cn } from '../ui/cn'
import { leadGenBaseUrl } from '../../lib/leadGenBaseUrl'

const LEAD_GEN_URL = leadGenBaseUrl()

// ── Integration catalogue ──────────────────────────────────────────────────────

type AuthMethod = 'oauth' | 'pat' | 'none'
type IntegrationStatus = 'live' | 'coming_soon'

interface Integration {
  id: string
  label: string
  icon: string
  description: string
  authMethod: AuthMethod
  oauthPath?: string       // path segment for /oauth/<oauthPath>/connect
  crmType?: string         // set for CRM integrations to call /crm/select
  hint?: string
  status: IntegrationStatus
}

interface Category {
  id: string
  label: string
  icon: string
  integrations: Integration[]
}

const CATEGORIES: Category[] = [
  {
    id: 'crm',
    label: 'CRM & Spreadsheets',
    icon: '📊',
    integrations: [
      {
        id: 'gsheets', label: 'Google Sheets', icon: '🟢', description: 'Spreadsheet',
        authMethod: 'oauth', oauthPath: 'gsheets', crmType: 'gsheets', status: 'live',
        hint: 'Authorize with Google — a new sheet is created automatically.',
      },
      {
        id: 'hubspot', label: 'HubSpot', icon: '🟠', description: 'CRM',
        authMethod: 'pat', crmType: 'hubspot', status: 'live',
        hint: 'Paste your Private App Token from HubSpot → Settings → Integrations → Private Apps.',
      },
      {
        id: 'notion', label: 'Notion', icon: '⬛', description: 'Database',
        authMethod: 'oauth', oauthPath: 'notion', crmType: 'notion', status: 'live',
        hint: 'Authorize with Notion to write leads to a database.',
      },
      {
        id: 'excel', label: 'Excel (OneDrive)', icon: '🔵', description: 'Spreadsheet',
        authMethod: 'oauth', oauthPath: 'excel', crmType: 'excel', status: 'live',
        hint: 'Authorize with Microsoft — a workbook is created in OneDrive.',
      },
    ],
  },
  {
    id: 'email',
    label: 'Email',
    icon: '📧',
    integrations: [
      {
        id: 'gmail', label: 'Gmail', icon: '✉️', description: 'Send & receive',
        authMethod: 'oauth', oauthPath: 'gmail', status: 'live',
        hint: 'Authorize Gmail so agents can send outreach emails on your behalf.',
      },
    ],
  },
  {
    id: 'messaging',
    label: 'Messaging',
    icon: '💬',
    integrations: [
      { id: 'whatsapp', label: 'WhatsApp',  icon: '💬', description: 'Business API', authMethod: 'none', status: 'coming_soon' },
      { id: 'telegram', label: 'Telegram',  icon: '✈️', description: 'Bot API',       authMethod: 'none', status: 'coming_soon' },
      { id: 'slack',    label: 'Slack',     icon: '💼', description: 'Workspace',     authMethod: 'none', status: 'coming_soon' },
      { id: 'discord',  label: 'Discord',   icon: '🎮', description: 'Server',        authMethod: 'none', status: 'coming_soon' },
    ],
  },
  {
    id: 'ecommerce',
    label: 'E-commerce',
    icon: '🛒',
    integrations: [
      { id: 'shopify',    label: 'Shopify',     icon: '🛍️', description: 'Store',    authMethod: 'none', status: 'coming_soon' },
      { id: 'stripe',     label: 'Stripe',      icon: '💳', description: 'Payments', authMethod: 'none', status: 'coming_soon' },
      { id: 'woocommerce',label: 'WooCommerce', icon: '🛒', description: 'Store',    authMethod: 'none', status: 'coming_soon' },
    ],
  },
  {
    id: 'social',
    label: 'Social Media',
    icon: '📣',
    integrations: [
      { id: 'linkedin',  label: 'LinkedIn',  icon: '💼', description: 'Network',  authMethod: 'none', status: 'coming_soon' },
      { id: 'twitter',   label: 'X / Twitter',icon: '𝕏', description: 'Timeline', authMethod: 'none', status: 'coming_soon' },
      { id: 'instagram', label: 'Instagram', icon: '📸', description: 'Feed',     authMethod: 'none', status: 'coming_soon' },
    ],
  },
]

// ── Tool status shape returned by /tool-settings/status ───────────────────────

interface ToolStatus {
  connected: boolean
  email?: string
  spreadsheet_id?: string
  database_id?: string
  workbook_name?: string
}

interface AllStatus {
  active_crm: string | null
  tools: Record<string, ToolStatus>
}

// ── Modal root ─────────────────────────────────────────────────────────────────

export function IntegrationsModal() {
  const store    = useSessionStore()
  const sessionId = store.sessionId
  const isOpen   = store.integrationsModalOpen

  const [allStatus, setAllStatus]     = useState<AllStatus | null>(null)
  const [loadingStatus, setLoading]   = useState(false)
  const [expanded, setExpanded]       = useState<string | null>(null)
  const [patToken, setPatToken]       = useState('')
  const [connecting, setConnecting]   = useState(false)
  const [justConnected, setJustConnected] = useState<string | null>(null)
  const [error, setError]             = useState<string | null>(null)
  const popupRef = useRef<Window | null>(null)
  const pollRef  = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchStatus = useCallback(async () => {
    if (!sessionId) return
    setLoading(true)
    try {
      const res = await fetch(
        `${LEAD_GEN_URL}/tool-settings/status?tenant_id=${encodeURIComponent(sessionId)}`,
      )
      if (res.ok) setAllStatus(await res.json())
    } catch { /* lead-gen may not be running */ }
    finally { setLoading(false) }
  }, [sessionId])

  useEffect(() => {
    if (isOpen) {
      setExpanded(null)
      setJustConnected(null)
      setError(null)
      setPatToken('')
      void fetchStatus()
    }
  }, [isOpen, fetchStatus])

  useEffect(() => {
    if (!isOpen) {
      if (pollRef.current) clearInterval(pollRef.current)
      popupRef.current?.close()
    }
  }, [isOpen])

  if (!isOpen) return null

  const tools = allStatus?.tools ?? {}
  const activeCrm = allStatus?.active_crm ?? null

  const connectedCount = Object.values(tools).filter((t) => t.connected).length

  const selectIntegration = (id: string) => {
    setExpanded((prev) => (prev === id ? null : id))
    setError(null)
    setPatToken('')
    setJustConnected(null)
  }

  // ── OAuth connect ────────────────────────────────────────────────────────────

  const connectOAuth = async (intg: Integration) => {
    if (!sessionId || !intg.oauthPath) return
    setConnecting(true)
    setError(null)
    try {
      const res = await fetch(
        `${LEAD_GEN_URL}/oauth/${intg.oauthPath}/connect?tenant_id=${encodeURIComponent(sessionId)}`,
      )
      if (!res.ok) throw new Error(`Could not get auth URL (${res.status})`)
      const data = await res.json()
      if (!data.auth_url) throw new Error('No auth_url returned')

      const popup = window.open(data.auth_url, 'intg_oauth', 'width=600,height=720,left=200,top=100')
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
          // For CRM integrations, activate it after OAuth
          if (intg.crmType) {
            await fetch(`${LEAD_GEN_URL}/crm/select`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ tenant_id: sessionId, crm_type: intg.crmType }),
            })
          }
          setJustConnected(intg.id)
          await fetchStatus()
          setExpanded(null)
        } catch {
          setError(`Authorized but could not activate ${intg.label} — try again.`)
        } finally {
          setConnecting(false)
        }
      }, 600)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'OAuth failed')
      setConnecting(false)
    }
  }

  // ── PAT connect (HubSpot) ────────────────────────────────────────────────────

  const connectPat = async (intg: Integration) => {
    if (!sessionId || !patToken.trim()) return
    setConnecting(true)
    setError(null)
    try {
      const res = await fetch(`${LEAD_GEN_URL}/crm/hubspot/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tenant_id: sessionId, token: patToken.trim() }),
      })
      if (!res.ok) throw new Error(`Server error ${res.status}`)
      if (intg.crmType) {
        await fetch(`${LEAD_GEN_URL}/crm/select`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tenant_id: sessionId, crm_type: intg.crmType }),
        })
      }
      setJustConnected(intg.id)
      setPatToken('')
      await fetchStatus()
      setExpanded(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to connect')
    } finally {
      setConnecting(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-label="Agent Integrations"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-surface-canvas/70"
        onClick={() => store.closeIntegrationsModal()}
        aria-hidden="true"
      />

      <div className="relative flex flex-col bg-surface-elevated border border-surface-border rounded-xl shadow-2xl overflow-hidden w-[680px] max-h-[88vh]">

        {/* Header */}
        <div className="flex items-center gap-3 px-5 h-[60px] border-b border-surface-border shrink-0 bg-surface-base">
          <div className="size-9 flex items-center justify-center rounded-lg bg-brand-primary-dim border border-[rgba(59,110,248,0.2)] text-base shrink-0">
            ⚡
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[14px] font-semibold text-text-heading leading-snug">
              Agent Integrations
            </p>
            <p className="text-[11px] text-text-secondary mt-px">
              {loadingStatus
                ? 'Checking connections…'
                : connectedCount > 0
                  ? `${connectedCount} integration${connectedCount !== 1 ? 's' : ''} connected`
                  : 'Give your agents access to tools & platforms'}
            </p>
          </div>
          <button
            onClick={() => store.closeIntegrationsModal()}
            className="text-text-disabled hover:text-text-secondary text-xl leading-none ml-2"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        {/* Body — scrollable */}
        <div className="flex-1 overflow-y-auto scrollbar-thin px-5 py-4 flex flex-col gap-5">

          {CATEGORIES.map((cat) => {
            const hasLive = cat.integrations.some((i) => i.status === 'live')
            return (
              <div key={cat.id}>
                {/* Category header */}
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-[13px]">{cat.icon}</span>
                  <p className="text-[11px] font-semibold text-text-secondary uppercase tracking-wide">
                    {cat.label}
                  </p>
                  {!hasLive && (
                    <span className="ml-auto text-[9px] font-semibold px-2 py-0.5 rounded-full bg-surface-overlay border border-surface-border text-text-disabled">
                      Coming Soon
                    </span>
                  )}
                </div>

                {/* Tiles */}
                <div className="grid grid-cols-4 gap-2">
                  {cat.integrations.map((intg) => {
                    const toolState = tools[intg.id]
                    const isConnected = Boolean(toolState?.connected)
                    const isActive    = intg.crmType ? activeCrm === intg.crmType : isConnected
                    const isExpanded  = expanded === intg.id
                    const wasJust     = justConnected === intg.id
                    const isComingSoon = intg.status === 'coming_soon'

                    return (
                      <button
                        key={intg.id}
                        type="button"
                        disabled={isComingSoon || connecting}
                        onClick={() => !isComingSoon && selectIntegration(intg.id)}
                        className={cn(
                          'flex flex-col items-start gap-1 px-3 py-2.5 rounded-lg border text-left transition-colors',
                          isComingSoon
                            ? 'border-surface-border bg-surface-canvas opacity-50 cursor-not-allowed'
                            : wasJust
                              ? 'border-semantic-success bg-semantic-successDim'
                              : isConnected
                                ? 'border-semantic-success/50 bg-semantic-successDim/60'
                                : isExpanded
                                  ? 'border-brand-primary bg-brand-primary/5'
                                  : 'border-surface-border bg-surface-base hover:border-surface-muted',
                        )}
                      >
                        <div className="flex items-center justify-between w-full">
                          <span className="text-base leading-none">{intg.icon}</span>
                          {isComingSoon ? (
                            <span className="text-[8px] text-text-disabled">Soon</span>
                          ) : isConnected ? (
                            <span className="text-[9px] font-bold text-semantic-success">✓</span>
                          ) : isExpanded ? (
                            <span className="size-1.5 rounded-full bg-brand-primary" />
                          ) : null}
                        </div>
                        <p className={cn(
                          'text-[11px] font-medium leading-tight',
                          isConnected ? 'text-semantic-success' : 'text-text-heading',
                        )}>
                          {intg.label}
                        </p>
                        <p className="text-[9px] text-text-disabled leading-none">{intg.description}</p>
                        {isActive && intg.crmType && (
                          <span className="text-[8px] font-semibold text-semantic-success">Active CRM</span>
                        )}
                      </button>
                    )
                  })}
                </div>

                {/* Expanded connection panel */}
                {cat.integrations.some((i) => i.id === expanded) && (() => {
                  const intg = cat.integrations.find((i) => i.id === expanded)!
                  const toolState = tools[intg.id]
                  const isConnected = Boolean(toolState?.connected)

                  return (
                    <div className="mt-2 rounded-lg border border-surface-border bg-surface-base px-4 py-3 flex flex-col gap-2.5">
                      <p className="text-[11px] font-semibold text-text-secondary uppercase tracking-wide">
                        {isConnected ? `Manage ${intg.label}` : `Connect ${intg.label}`}
                      </p>

                      {/* Detail rows for connected state */}
                      {isConnected && (
                        <div className="flex flex-col gap-1 text-[12px] text-text-secondary">
                          {toolState?.email && <p>Account: <span className="text-text-body">{toolState.email}</span></p>}
                          {toolState?.spreadsheet_id && <p>Sheet ID: <span className="text-text-body font-mono text-[11px]">{toolState.spreadsheet_id}</span></p>}
                          {toolState?.database_id && <p>Database ID: <span className="text-text-body font-mono text-[11px]">{toolState.database_id}</span></p>}
                          {toolState?.workbook_name && <p>Workbook: <span className="text-text-body">{toolState.workbook_name}</span></p>}
                        </div>
                      )}

                      {intg.hint && (
                        <p className="text-[12px] text-text-secondary leading-relaxed">{intg.hint}</p>
                      )}

                      {intg.authMethod === 'pat' ? (
                        <div className="flex flex-col gap-2">
                          <input
                            type="password"
                            value={patToken}
                            onChange={(e) => setPatToken(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && connectPat(intg)}
                            placeholder="pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                            autoFocus
                            className="h-9 px-3 rounded-md bg-surface-canvas border border-surface-borderLight text-[12px] text-text-body placeholder:text-text-disabled focus:outline-none focus:border-brand-primary font-mono"
                          />
                          <Button
                            size="sm"
                            onClick={() => connectPat(intg)}
                            loading={connecting}
                            disabled={!patToken.trim()}
                            className="self-start bg-brand-primary hover:bg-brand-primary-hover text-white border-0"
                          >
                            {isConnected ? 'Update Token' : `Connect ${intg.label}`}
                          </Button>
                        </div>
                      ) : intg.authMethod === 'oauth' ? (
                        <Button
                          size="sm"
                          onClick={() => connectOAuth(intg)}
                          loading={connecting}
                          className="self-start bg-brand-primary hover:bg-brand-primary-hover text-white border-0"
                        >
                          {connecting
                            ? `Waiting for ${intg.label}…`
                            : isConnected
                              ? `Re-authorize ${intg.label}`
                              : `Connect ${intg.label}`}
                        </Button>
                      ) : null}

                      {error && (
                        <p className="text-[12px] text-semantic-error px-3 py-2 rounded-md bg-semantic-errorDim border border-[rgba(239,68,68,0.25)]">
                          {error}
                        </p>
                      )}
                    </div>
                  )
                })()}
              </div>
            )
          })}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-5 py-3.5 border-t border-surface-border shrink-0 bg-surface-base">
          <p className="text-[11px] text-text-disabled">
            More integrations shipping soon — requests welcome
          </p>
          <Button
            size="sm"
            onClick={() => store.closeIntegrationsModal()}
            className="bg-surface-overlay border border-surface-borderLight text-text-body hover:border-surface-muted"
          >
            Done
          </Button>
        </div>
      </div>
    </div>
  )
}
