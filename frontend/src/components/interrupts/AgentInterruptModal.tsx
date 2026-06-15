/**
 * AgentInterruptModal — unified interrupt UI layer for all agents.
 *
 * Every interrupt type (OAuth, credential form, HITL approval with email
 * drafts, clarification) is rendered inside one consistent modal shell so
 * that onboarding a new agent only requires adding its interrupt_type here.
 *
 * The shell provides:
 *   • Agent identity header (avatar, name, interrupt-type badge)
 *   • Scrollable body (type-specific content)
 *   • Action footer (type-specific buttons)
 *
 * Resume logic and streaming callbacks are unchanged from the previous
 * per-modal implementations — only presentation is unified.
 */
import { useEffect, useRef, useState } from 'react'
import type {
  AgentClarificationMetadata,
  AgentOAuthCallbackMetadata,
  AuthCallbackMetadata,
  AuthFormSubmissionMetadata,
  CrmSetupMetadata,
  HitlApprovalMetadata,
  HitlClarificationMetadata,
  Interrupt,
} from '../../types'
import { sessions } from '../../api/client'
import { leadGenBaseUrl } from '../../lib/leadGenBaseUrl'
import { Button } from '../ui/Button'
import { cn } from '../ui/cn'

// ── Shared props ───────────────────────────────────────────────────────────────

interface InterruptProps {
  interrupt: Interrupt
  sessionId: string
  streamResponse: (res: Response) => Promise<void>
  onAfterStream: () => Promise<void>
}

// ── Interrupt type metadata ────────────────────────────────────────────────────

interface TypeConfig {
  icon: string
  title: (meta: Record<string, unknown>) => string
  badge: string
  badgeColor: string
  /** Width class for the modal */
  width: (meta: Record<string, unknown>) => string
  /** Whether backdrop click dismisses (false for mandatory interrupts) */
  dismissible: boolean
}

const TYPE_CONFIG: Record<string, TypeConfig> = {
  AUTH_FORM_SUBMISSION: {
    icon: '🔐',
    title: (m) => (m.form_title as string) || 'Credential Required',
    badge: 'Credential',
    badgeColor: 'bg-semantic-warningDim text-semantic-warning border-[rgba(245,158,11,0.3)]',
    width: () => 'w-[460px]',
    dismissible: false,
  },
  HITL_APPROVAL: {
    icon: '✉️',
    title: (m) => (Array.isArray(m.drafts) && m.drafts.length > 0)
      ? 'Review Outreach Emails'
      : 'Approval Required',
    badge: 'Approval',
    badgeColor: 'bg-semantic-warningDim text-semantic-warning border-[rgba(245,158,11,0.3)]',
    width: (m) => (Array.isArray(m.drafts) && m.drafts.length > 0) ? 'w-[640px]' : 'w-[460px]',
    dismissible: false,
  },
  AUTH_CALLBACK: {
    icon: '🔗',
    title: (m) => `Connect to ${(m.provider_name as string) || 'OAuth Provider'}`,
    badge: 'Authorization',
    badgeColor: 'bg-brand-primary-dim text-brand-primary-light border-[rgba(59,110,248,0.3)]',
    width: () => 'w-[460px]',
    dismissible: false,
  },
  AGENT_OAUTH_CALLBACK: {
    icon: '🔗',
    title: (m) => `Connect to ${(m.provider_name as string) || 'OAuth Provider'}`,
    badge: 'Authorization',
    badgeColor: 'bg-brand-primary-dim text-brand-primary-light border-[rgba(59,110,248,0.3)]',
    width: () => 'w-[460px]',
    dismissible: false,
  },
  HITL_CLARIFICATION: {
    icon: '💬',
    title: () => 'Input Required',
    badge: 'Clarification',
    badgeColor: 'bg-semantic-warningDim text-semantic-warning border-[rgba(245,158,11,0.3)]',
    width: () => 'w-[460px]',
    dismissible: false,
  },
  AGENT_CLARIFICATION: {
    icon: '💬',
    title: () => 'Agent Input Required',
    badge: 'Clarification',
    badgeColor: 'bg-semantic-warningDim text-semantic-warning border-[rgba(245,158,11,0.3)]',
    width: () => 'w-[460px]',
    dismissible: false,
  },
  CRM_SETUP: {
    icon: '🗃',
    title: () => 'Connect a CRM',
    badge: 'CRM Setup',
    badgeColor: 'bg-brand-primary-dim text-brand-primary-light border-[rgba(59,110,248,0.3)]',
    width: () => 'w-[560px]',
    dismissible: false,
  },
}

const FALLBACK_CONFIG: TypeConfig = {
  icon: '⚡',
  title: () => 'Agent Request',
  badge: 'Interrupt',
  badgeColor: 'bg-surface-overlay text-text-secondary border-surface-border',
  width: () => 'w-[460px]',
  dismissible: false,
}

// ── Shell ──────────────────────────────────────────────────────────────────────

export function AgentInterruptModal(props: InterruptProps) {
  const { interrupt } = props
  const meta = interrupt.metadata as Record<string, unknown>
  const cfg = TYPE_CONFIG[interrupt.interrupt_type] ?? FALLBACK_CONFIG

  const agentName =
    (meta.agent_display_name as string) ||
    (meta.provider_name as string) ||
    'Agent'

  const title = cfg.title(meta)
  const modalWidth = cfg.width(meta)

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-surface-canvas/70" aria-hidden="true" />

      <div
        className={cn(
          'relative flex flex-col bg-surface-elevated border border-surface-border',
          'rounded-xl shadow-2xl overflow-hidden max-h-[88vh]',
          modalWidth,
        )}
      >
        {/* ── Header ── */}
        <div className="flex items-center gap-3 px-5 h-[60px] border-b border-surface-border shrink-0 bg-surface-base">
          {/* Agent avatar */}
          <div
            className={cn(
              'size-9 flex items-center justify-center rounded-lg shrink-0',
              'bg-brand-primary-dim border border-[rgba(59,110,248,0.2)] text-base',
            )}
            aria-hidden="true"
          >
            {cfg.icon}
          </div>

          {/* Title + agent name */}
          <div className="flex-1 min-w-0">
            <p className="text-[14px] font-semibold text-text-heading leading-snug truncate">
              {title}
            </p>
            <p className="text-[11px] text-text-secondary truncate leading-tight mt-px">
              {agentName}
            </p>
          </div>

          {/* Interrupt type badge */}
          <span
            className={cn(
              'shrink-0 text-[10px] font-semibold px-2 py-0.5 rounded-full border',
              cfg.badgeColor,
            )}
          >
            {cfg.badge}
          </span>
        </div>

        {/* ── Scrollable body ── */}
        <div className="flex-1 overflow-y-auto scrollbar-thin">
          <InterruptBody {...props} />
        </div>
      </div>
    </div>
  )
}

// ── Body router ────────────────────────────────────────────────────────────────

function InterruptBody(props: InterruptProps) {
  switch (props.interrupt.interrupt_type) {
    case 'AUTH_FORM_SUBMISSION':
      return <CredentialBody {...props} />
    case 'HITL_APPROVAL':
      return <ApprovalBody {...props} />
    case 'AUTH_CALLBACK':
    case 'AGENT_OAUTH_CALLBACK':
      return <OAuthBody {...props} />
    case 'CRM_SETUP':
      return <CrmSetupBody {...props} />
    case 'HITL_CLARIFICATION':
    case 'AGENT_CLARIFICATION':
    default:
      return <ClarificationBody {...props} />
  }
}

// ── Shared section primitives ──────────────────────────────────────────────────

function Section({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn('px-5 py-4 flex flex-col gap-3', className)}>{children}</div>
}

function Footer({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 px-5 py-4 border-t border-surface-border shrink-0 bg-surface-base">
      {children}
    </div>
  )
}

function ErrorNote({ msg }: { msg: string }) {
  return (
    <p className="text-[12px] text-semantic-error px-3 py-2 rounded-md bg-semantic-errorDim border border-[rgba(239,68,68,0.25)]">
      {msg}
    </p>
  )
}

// ── 1. Credential body (AUTH_FORM_SUBMISSION) ──────────────────────────────────

function CredentialBody({ interrupt, sessionId, streamResponse, onAfterStream }: InterruptProps) {
  const meta = interrupt.metadata as Partial<AuthFormSubmissionMetadata>
  const fieldLabel = meta.field_label ?? 'API Key'
  const isSecret = meta.is_secret !== false

  const [value, setValue] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async () => {
    if (!value.trim()) return
    setSubmitting(true)
    setError(null)
    try {
      const res = await sessions.resume(
        sessionId,
        interrupt.interrupt_id,
        interrupt.interrupt_type,
        { status: 'complete', credential_value: value.trim(), vault_key: meta.vault_key ?? '' },
      )
      if (res.ok) {
        await streamResponse(res)
        await onAfterStream()
      } else {
        setError(`Server error (${res.status})`)
      }
    } catch {
      setError('Could not reach the server')
    } finally {
      setSubmitting(false)
    }
  }

  const deny = async () => {
    try {
      const res = await sessions.resume(
        sessionId,
        interrupt.interrupt_id,
        interrupt.interrupt_type,
        { status: 'denied' },
      )
      if (res.ok) {
        await streamResponse(res)
        await onAfterStream()
      }
    } catch { /* ignore */ }
  }

  return (
    <>
      <Section>
        <p className="text-[13px] text-text-body leading-relaxed">{interrupt.message}</p>
        <div className="flex flex-col gap-1.5">
          <label className="text-[12px] font-semibold text-text-secondary uppercase tracking-wide">
            {fieldLabel}
          </label>
          <input
            type={isSecret ? 'password' : 'text'}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && submit()}
            placeholder="Paste value…"
            autoFocus
            className="h-10 px-3 rounded-lg bg-surface-canvas border border-surface-borderLight text-[13px] text-text-body placeholder:text-text-disabled focus:outline-none focus:border-brand-primary font-mono"
          />
        </div>
        {error && <ErrorNote msg={error} />}
      </Section>

      <Footer>
        <Button
          size="sm"
          onClick={deny}
          disabled={submitting}
          className="flex-1 bg-surface-overlay border border-surface-borderLight text-text-body hover:border-surface-muted"
        >
          Deny
        </Button>
        <Button
          size="sm"
          onClick={submit}
          loading={submitting}
          disabled={!value.trim()}
          className="flex-1 bg-brand-primary hover:bg-brand-primary-hover text-white border-0"
        >
          Submit
        </Button>
      </Footer>
    </>
  )
}

// ── 2. Approval body (HITL_APPROVAL) ──────────────────────────────────────────

interface EmailDraft {
  to: string
  subject: string
  body: string
  first_name?: string
  company?: string
  [key: string]: unknown
}

const RISK_STYLES: Record<string, string> = {
  low: 'bg-semantic-successDim text-semantic-success border-[rgba(34,197,94,0.3)]',
  medium: 'bg-semantic-warningDim text-semantic-warning border-[rgba(245,158,11,0.3)]',
  high: 'bg-semantic-errorDim text-semantic-error border-[rgba(239,68,68,0.3)]',
}

function ApprovalBody({ interrupt, sessionId, streamResponse, onAfterStream }: InterruptProps) {
  const meta = interrupt.metadata as Partial<HitlApprovalMetadata> & {
    drafts?: EmailDraft[]
    risk_level?: string
  }

  const rawDrafts: EmailDraft[] = meta.drafts ?? []
  const [drafts, setDrafts] = useState<EmailDraft[]>(rawDrafts)
  const [expandedIdx, setExpandedIdx] = useState<number | null>(rawDrafts.length > 0 ? 0 : null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const hasDrafts = drafts.length > 0
  const riskLevel = meta.risk_level ?? 'medium'
  const riskStyle = RISK_STYLES[riskLevel] ?? RISK_STYLES.medium
  const riskLabel = riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1) + ' Risk'
  const actionDescription = meta.action_description ?? interrupt.message
  const capabilityName = (meta as Record<string, unknown>).capability_name as string | undefined

  const updateDraft = (idx: number, field: 'subject' | 'body', val: string) =>
    setDrafts((prev) => prev.map((d, i) => (i === idx ? { ...d, [field]: val } : d)))

  const resume = async (approved: boolean) => {
    setSubmitting(true)
    setError(null)
    try {
      const payload: Record<string, unknown> = { status: approved ? 'approved' : 'denied' }
      if (approved && hasDrafts) payload.edited_drafts = drafts
      const res = await sessions.resume(
        sessionId,
        interrupt.interrupt_id,
        interrupt.interrupt_type,
        payload,
      )
      if (res.ok) {
        await streamResponse(res)
        await onAfterStream()
      } else {
        setError(`Server error (${res.status})`)
        setSubmitting(false)
      }
    } catch {
      setError('Could not reach the server')
      setSubmitting(false)
    }
  }

  return (
    <>
      <Section>
        {/* Risk + action description */}
        <div className="flex items-start gap-3">
          <div className="flex-1 min-w-0">
            <p className="text-[13px] text-text-body leading-relaxed">{actionDescription}</p>
            {capabilityName && !hasDrafts && (
              <p className="text-[11px] text-text-secondary mt-1">
                <span className="font-medium">Capability:</span> {capabilityName}
              </p>
            )}
          </div>
          <span className={cn('shrink-0 text-[10px] font-semibold px-2 py-0.5 rounded-full border', riskStyle)}>
            {riskLabel}
          </span>
        </div>

        {/* Email draft cards */}
        {hasDrafts && (
          <div className="flex flex-col gap-2 mt-1">
            <p className="text-[11px] text-text-secondary">
              Review and optionally edit each email before sending.
            </p>
            {drafts.map((draft, idx) => (
              <div
                key={idx}
                className="rounded-lg border border-surface-border bg-surface-base overflow-hidden"
              >
                <button
                  type="button"
                  onClick={() => setExpandedIdx(expandedIdx === idx ? null : idx)}
                  className="w-full flex items-center gap-2 px-4 py-2.5 text-left hover:bg-surface-overlay transition-colors"
                >
                  <span className="text-[10px] font-bold text-text-disabled shrink-0 tabular-nums">
                    #{idx + 1}
                  </span>
                  <span className="text-[13px] text-text-body truncate flex-1">
                    {draft.to || draft.first_name || `Email ${idx + 1}`}
                    {draft.company ? (
                      <span className="text-text-secondary"> · {draft.company}</span>
                    ) : null}
                  </span>
                  <span className="text-[10px] text-text-disabled shrink-0">
                    {expandedIdx === idx ? '▲' : '▼'}
                  </span>
                </button>

                {expandedIdx === idx && (
                  <div className="px-4 pb-4 flex flex-col gap-2.5 border-t border-surface-border">
                    {/* To (read-only) */}
                    <div className="flex flex-col gap-0.5 mt-3">
                      <span className="text-[10px] font-semibold text-text-disabled uppercase tracking-wide">To</span>
                      <p className="text-[13px] text-text-body">{draft.to || '—'}</p>
                    </div>
                    {/* Subject */}
                    <div className="flex flex-col gap-0.5">
                      <span className="text-[10px] font-semibold text-text-disabled uppercase tracking-wide">Subject</span>
                      <input
                        value={draft.subject ?? ''}
                        onChange={(e) => updateDraft(idx, 'subject', e.target.value)}
                        className="h-8 px-3 rounded-md bg-surface-canvas border border-surface-borderLight text-[13px] text-text-body focus:outline-none focus:border-brand-primary"
                      />
                    </div>
                    {/* Body */}
                    <div className="flex flex-col gap-0.5">
                      <span className="text-[10px] font-semibold text-text-disabled uppercase tracking-wide">Body</span>
                      <textarea
                        value={draft.body ?? ''}
                        onChange={(e) => updateDraft(idx, 'body', e.target.value)}
                        rows={5}
                        className="px-3 py-2 rounded-md bg-surface-canvas border border-surface-borderLight text-[13px] text-text-body focus:outline-none focus:border-brand-primary resize-none"
                      />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {error && <ErrorNote msg={error} />}
      </Section>

      <Footer>
        <Button
          size="sm"
          onClick={() => resume(false)}
          disabled={submitting}
          className="flex-1 bg-surface-overlay border border-surface-borderLight text-text-body hover:border-surface-muted"
        >
          {hasDrafts ? 'Cancel' : 'Deny'}
        </Button>
        <Button
          size="sm"
          onClick={() => resume(true)}
          loading={submitting}
          className="flex-1 bg-semantic-success hover:bg-semantic-success/90 text-white border-0"
        >
          {hasDrafts ? `Send ${drafts.length} Email${drafts.length !== 1 ? 's' : ''}` : 'Approve'}
        </Button>
      </Footer>
    </>
  )
}

// ── 3. OAuth body (AUTH_CALLBACK / AGENT_OAUTH_CALLBACK) ───────────────────────

function OAuthBody({ interrupt, sessionId, streamResponse, onAfterStream }: InterruptProps) {
  const meta = interrupt.metadata as Partial<AuthCallbackMetadata & AgentOAuthCallbackMetadata>
  const authUrl = meta.auth_url ?? ''
  const providerName = meta.provider_name ?? 'OAuth Provider'
  const scopes = meta.scopes ?? []

  const [opened, setOpened] = useState(false)
  const [waitingClose, setWaitingClose] = useState(false)
  const [resuming, setResuming] = useState(false)
  const [denying, setDenying] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const popupRef = useRef<Window | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current) }, [])

  const sendResume = () => {
    if (pollRef.current) clearInterval(pollRef.current)
    setWaitingClose(false)
    setResuming(true)
    sessions
      .resume(sessionId, interrupt.interrupt_id, interrupt.interrupt_type, { status: 'granted' })
      .then((res) => { if (res.ok) return streamResponse(res) })
      .then(() => onAfterStream())
      .catch(() => setResuming(false))
  }

  const openPopup = () => {
    setError(null)
    const popup = window.open(authUrl, 'emerge_oauth', 'width=600,height=720,left=200,top=100')
    if (!popup) { setError('blocked'); return }
    popupRef.current = popup
    setOpened(true)
    setWaitingClose(true)
    pollRef.current = setInterval(() => {
      try { if (popup.closed) sendResume() } catch { /* cross-origin — keep polling */ }
    }, 500)
  }

  const deny = async () => {
    if (pollRef.current) clearInterval(pollRef.current)
    setDenying(true)
    try {
      const res = await sessions.resume(
        sessionId,
        interrupt.interrupt_id,
        interrupt.interrupt_type,
        { status: 'denied' },
      )
      if (res.ok) await onAfterStream()
    } catch { /* ignore */ }
    setDenying(false)
  }

  return (
    <>
      <Section>
        <p className="text-[13px] text-text-body leading-relaxed">{interrupt.message}</p>

        {scopes.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {scopes.map((s) => (
              <span
                key={s}
                className="px-2 py-0.5 rounded-full bg-surface-overlay border border-surface-borderLight text-[11px] text-text-secondary font-mono"
              >
                {s}
              </span>
            ))}
          </div>
        )}

        {error === 'blocked' && (
          <div className="px-3 py-2.5 rounded-lg bg-semantic-errorDim border border-[rgba(239,68,68,0.25)] text-[12px] text-semantic-error flex flex-col gap-1">
            <span>Popup was blocked by your browser.</span>
            <a
              href={authUrl}
              target="_blank"
              rel="noreferrer"
              className="underline font-medium"
            >
              Open authorization page in a new tab
            </a>
            <span className="text-text-secondary">Then click "I've authorized" below once done.</span>
          </div>
        )}

        {waitingClose && (
          <div className="px-3 py-2.5 rounded-lg bg-brand-primary-dim border border-[rgba(59,110,248,0.2)] text-[12px] text-brand-primary-light flex items-center gap-2">
            <span className="size-3 rounded-full border-2 border-current border-t-transparent animate-spin shrink-0" />
            Waiting for authorization window to close…
          </div>
        )}
      </Section>

      <Footer>
        <Button
          size="sm"
          onClick={deny}
          loading={denying}
          disabled={resuming}
          className="bg-surface-overlay border border-surface-borderLight text-text-body hover:border-surface-muted"
        >
          Deny
        </Button>

        {waitingClose || error === 'blocked' ? (
          <Button
            size="sm"
            onClick={sendResume}
            loading={resuming}
            className="flex-1 bg-brand-primary hover:bg-brand-primary-hover text-white border-0"
          >
            I've authorized — continue
          </Button>
        ) : (
          <Button
            size="sm"
            onClick={openPopup}
            disabled={!authUrl || resuming}
            className="flex-1 bg-brand-primary hover:bg-brand-primary-hover text-white border-0"
          >
            {opened ? `Reopen ${providerName}` : `Connect to ${providerName}`}
          </Button>
        )}
      </Footer>
    </>
  )
}

// ── 4. CRM setup body (CRM_SETUP) ─────────────────────────────────────────────

type CrmOption = {
  id: string
  label: string
  icon: string
  authMethod: 'pat' | 'oauth'
  oauthPath?: string
  description: string
  hint: string
}

const CRM_OPTIONS: CrmOption[] = [
  {
    id: 'gsheets', label: 'Google Sheets', icon: '🟢', authMethod: 'oauth', oauthPath: 'gsheets',
    description: 'Spreadsheet', hint: 'Authorize with your Google account — a new sheet is created automatically.',
  },
  {
    id: 'hubspot', label: 'HubSpot', icon: '🟠', authMethod: 'pat',
    description: 'CRM', hint: 'Paste your Private App Token from HubSpot → Settings → Integrations → Private Apps.',
  },
  {
    id: 'notion', label: 'Notion', icon: '⬛', authMethod: 'oauth', oauthPath: 'notion',
    description: 'Database', hint: 'Authorize with your Notion account to write leads to a database.',
  },
  {
    id: 'excel', label: 'Excel (OneDrive)', icon: '🔵', authMethod: 'oauth', oauthPath: 'excel',
    description: 'Spreadsheet', hint: 'Authorize with your Microsoft account — a workbook is created in OneDrive.',
  },
]

function CrmSetupBody({ interrupt, sessionId, streamResponse, onAfterStream }: InterruptProps) {
  const meta = interrupt.metadata as Partial<CrmSetupMetadata>
  const leadGenUrl = meta.lead_gen_url ?? leadGenBaseUrl()
  const tenantId   = meta.tenant_id ?? sessionId

  const [selected, setSelected]    = useState<string | null>('gsheets')
  const [patToken, setPatToken]     = useState('')
  const [connecting, setConnecting] = useState(false)
  const [connected, setConnected]   = useState<string | null>(null)
  const [error, setError]           = useState<string | null>(null)
  const [resuming, setResuming]     = useState(false)
  const [denying, setDenying]       = useState(false)
  const popupRef = useRef<Window | null>(null)
  const pollRef  = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current) }, [])

  const selectCrm = (id: string) => {
    if (connected) return
    setSelected(id)
    setError(null)
    setPatToken('')
  }

  const connectPat = async () => {
    if (!patToken.trim() || !selected) return
    setConnecting(true)
    setError(null)
    try {
      const res = await fetch(`${leadGenUrl}/crm/hubspot/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tenant_id: tenantId, token: patToken.trim() }),
      })
      if (!res.ok) throw new Error(`Server error ${res.status}`)
      await fetch(`${leadGenUrl}/crm/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tenant_id: tenantId, crm_type: selected }),
      })
      setConnected(selected)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to connect')
    } finally {
      setConnecting(false)
    }
  }

  const connectOAuth = async (opt: CrmOption) => {
    setConnecting(true)
    setError(null)
    try {
      const res = await fetch(
        `${leadGenUrl}/oauth/${opt.oauthPath}/connect?tenant_id=${encodeURIComponent(tenantId)}`,
      )
      if (!res.ok) throw new Error(`Could not get auth URL (${res.status})`)
      const data = await res.json()
      if (!data.auth_url) throw new Error('No auth_url returned')

      const popup = window.open(data.auth_url, 'crm_oauth', 'width=600,height=720,left=200,top=100')
      if (!popup) { setError('Popup blocked — allow popups and try again.'); setConnecting(false); return }
      popupRef.current = popup

      pollRef.current = setInterval(async () => {
        if (!popup.closed) return
        if (pollRef.current) clearInterval(pollRef.current)
        try {
          await fetch(`${leadGenUrl}/crm/select`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tenant_id: tenantId, crm_type: opt.id }),
          })
          setConnected(opt.id)
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

  const resume = async () => {
    setResuming(true)
    setError(null)
    try {
      const res = await sessions.resume(
        sessionId, interrupt.interrupt_id, interrupt.interrupt_type, { status: 'complete' },
      )
      if (res.ok) {
        await streamResponse(res)
        await onAfterStream()
      } else {
        setError(`Server error (${res.status})`)
        setResuming(false)
      }
    } catch {
      setError('Could not reach the server')
      setResuming(false)
    }
  }

  const skip = async () => {
    setDenying(true)
    try {
      const res = await sessions.resume(
        sessionId, interrupt.interrupt_id, interrupt.interrupt_type, { status: 'denied' },
      )
      if (res.ok) await onAfterStream()
    } catch { /* ignore */ }
    setDenying(false)
  }

  const selectedOpt = CRM_OPTIONS.find((o) => o.id === selected)
  const connectedOpt = CRM_OPTIONS.find((o) => o.id === connected)

  return (
    <>
      <Section>
        <p className="text-[13px] text-text-body leading-relaxed">{interrupt.message}</p>

        {/* Step 1 — CRM picker */}
        <div>
          <p className="text-[11px] font-semibold text-text-secondary uppercase tracking-wide mb-2">
            Step 1 — Choose a destination
          </p>
          <div className="grid grid-cols-2 gap-2">
            {CRM_OPTIONS.map((opt) => {
              const isActive    = selected === opt.id
              const isConnected = connected === opt.id
              return (
                <button
                  key={opt.id}
                  type="button"
                  disabled={!!connected}
                  onClick={() => selectCrm(opt.id)}
                  className={cn(
                    'flex items-center gap-2.5 px-3 py-2.5 rounded-lg border text-left transition-colors',
                    isConnected
                      ? 'border-semantic-success bg-semantic-successDim cursor-default'
                      : isActive
                        ? 'border-brand-primary bg-brand-primary/5'
                        : 'border-surface-border bg-surface-base hover:border-surface-muted',
                  )}
                >
                  <span className="text-base shrink-0">{opt.icon}</span>
                  <div className="min-w-0">
                    <p className={cn('text-[13px] font-medium leading-snug', isConnected ? 'text-semantic-success' : 'text-text-heading')}>
                      {opt.label}
                    </p>
                    <p className="text-[10px] text-text-secondary">{opt.description}</p>
                  </div>
                  {isConnected && (
                    <span className="ml-auto text-[9px] font-bold text-semantic-success shrink-0">✓</span>
                  )}
                  {isActive && !isConnected && (
                    <span className="ml-auto size-2.5 rounded-full bg-brand-primary shrink-0" />
                  )}
                </button>
              )
            })}
          </div>
        </div>

        {/* Step 2 — connection panel, shown once a CRM is selected */}
        {selectedOpt && !connected && (
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

        {/* Success banner */}
        {connectedOpt && (
          <div className="flex items-center gap-2 px-3 py-2.5 rounded-lg bg-semantic-successDim border border-[rgba(34,197,94,0.3)] text-[13px] text-semantic-success">
            <span className="text-base">{connectedOpt.icon}</span>
            <span><span className="font-semibold">{connectedOpt.label}</span> connected — click Continue to save your leads.</span>
          </div>
        )}

        {error && <ErrorNote msg={error} />}
      </Section>

      <Footer>
        <Button
          size="sm"
          onClick={skip}
          loading={denying}
          disabled={resuming}
          className="bg-surface-overlay border border-surface-borderLight text-text-body hover:border-surface-muted"
        >
          Skip
        </Button>
        <Button
          size="sm"
          onClick={resume}
          loading={resuming}
          disabled={!connected || denying}
          className={cn(
            'flex-1 border-0 text-white',
            connected ? 'bg-semantic-success hover:bg-semantic-success/90' : 'bg-surface-overlay text-text-disabled cursor-not-allowed',
          )}
        >
          {connected ? 'Continue — save leads' : 'Connect a CRM first'}
        </Button>
      </Footer>
    </>
  )
}

// ── 4. Clarification body (HITL_CLARIFICATION / AGENT_CLARIFICATION) ───────────

function ClarificationBody({ interrupt, sessionId, streamResponse, onAfterStream }: InterruptProps) {
  const meta = interrupt.metadata as Partial<HitlClarificationMetadata & AgentClarificationMetadata>
  const question = meta.question ?? interrupt.message

  const [value, setValue] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async () => {
    if (!value.trim()) return
    setSubmitting(true)
    setError(null)
    try {
      const res = await sessions.resume(
        sessionId,
        interrupt.interrupt_id,
        interrupt.interrupt_type,
        { status: 'complete', response: value.trim() },
      )
      if (res.ok) {
        await streamResponse(res)
        await onAfterStream()
      } else {
        setError(`Server error (${res.status})`)
      }
    } catch {
      setError('Could not reach the server')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <Section>
        <p className="text-[13px] text-text-body leading-relaxed">{question}</p>

        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void submit() }
          }}
          placeholder="Your response… (Enter to submit, Shift+Enter for new line)"
          autoFocus
          rows={3}
          className="w-full px-3 py-2.5 rounded-lg bg-surface-canvas border border-surface-borderLight text-[13px] text-text-body placeholder:text-text-disabled focus:outline-none focus:border-brand-primary resize-none"
        />

        {error && <ErrorNote msg={error} />}
      </Section>

      <Footer>
        <Button
          size="sm"
          onClick={submit}
          loading={submitting}
          disabled={!value.trim()}
          className="flex-1 bg-brand-primary hover:bg-brand-primary-hover text-white border-0"
        >
          Submit
        </Button>
      </Footer>
    </>
  )
}
