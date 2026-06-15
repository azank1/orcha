import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { Sidebar } from '../components/layout/Sidebar'
import { SessionListPanel } from '../components/layout/SessionListPanel'
import { RightPanel } from '../components/layout/RightPanel'
import { ToolTimelineRow } from '../components/chat/ExecutionTimeline'
import { MessageBubble } from '../components/chat/MessageBubble'
import { StreamingDots } from '../components/chat/StreamingDots'
import { InputBar } from '../components/ui/InputBar'
import { CredentialsModal } from '../components/modals/CredentialsModal'
import { SaveWorkflowModal } from '../components/modals/SaveWorkflowModal'
import { CrmSetupModal } from '../components/modals/CrmSetupModal'
import { IntegrationsModal } from '../components/modals/IntegrationsModal'
import { useSessionStore } from '../store/session'
import { useSessionSidebarStore } from '../store/sessionSidebar'
import { useAuthStore } from '../store/auth'
import { sessions, files } from '../api/client'
import { useSSE } from '../hooks/useSSE'
import { useSessionStatusSync } from '../hooks/useSessionStatusSync'
import { cn } from '../components/ui/cn'
import { buildChatTimeline } from '../lib/buildChatTimeline'
import { queryClient } from '../lib/queryClient'
import type {
  AgentClarificationMetadata,
  AttachedArtifactRef,
  HitlClarificationMetadata,
  Interrupt,
  InsufficientCreditsMetadata,
  PendingArtifact,
} from '../types'
import { HitlApprovalModal } from '../components/modals/HitlApprovalModal'
import { OAuthPopupHandler } from '../components/modals/OAuthPopupHandler'
import { InterruptCredentialModal } from '../components/modals/InterruptCredentialModal'
import { AgentInterruptModal } from '../components/interrupts/AgentInterruptModal'
import { leadGenBaseUrl } from '../lib/leadGenBaseUrl'

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  idle: { label: '● ready', color: 'text-text-secondary' },
  running: { label: '● running', color: 'text-brand-primary-light' },
  interrupted: { label: '● interrupted', color: 'text-semantic-warning' },
  complete: { label: '● complete', color: 'text-semantic-success' },
  failed: { label: '● failed', color: 'text-semantic-error' },
}

export function Chat() {
  const { sessionId: urlSessionId } = useParams<{ sessionId: string }>()
  const [input, setInput] = useState('')
  const [pendingArtifacts, setPendingArtifacts] = useState<PendingArtifact[]>([])
  const bottomRef = useRef<HTMLDivElement>(null)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const sessionSidebarOpen = useSessionSidebarStore((s) => s.isOpen)

  const store = useSessionStore()
  const { streamResponse, abort } = useSSE()
  const { refetchSessionDetails } = useSessionStatusSync()

  const chatTimeline = useMemo(
    () => buildChatTimeline(store.messages, store.toolTrace),
    [store.messages, store.toolTrace],
  )

  const { data: transcriptData } = useQuery({
    queryKey: ['transcript', urlSessionId],
    queryFn: () => sessions.getTranscript(urlSessionId!),
    enabled: Boolean(urlSessionId && isAuthenticated),
    staleTime: 15_000,
  })

  useEffect(() => {
    if (!urlSessionId) return
    const st = useSessionStore.getState()
    if (st.sessionId === urlSessionId) return
    st.reset()
    st.setSessionId(urlSessionId)
  }, [urlSessionId])

  useEffect(() => {
    if (!urlSessionId || !transcriptData?.entries?.length) return
    const s = useSessionStore.getState()
    if (s.sessionId !== urlSessionId) return
    if (s.streamingMessageId || s.status === 'running') return
    s.hydrateFromTranscript(urlSessionId, transcriptData.entries)
  }, [urlSessionId, transcriptData])

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [
    chatTimeline.length,
    store.streamingMessageId,
    store.messages.length,
    store.toolTrace.length,
  ])

  /** Shared post-resume / post-stream callback used by all interrupt handlers. */
  const onAfterInterrupt = useCallback(async () => {
    await refetchSessionDetails()
    void queryClient.invalidateQueries({ queryKey: ['transcript', store.sessionId] })
    void queryClient.invalidateQueries({ queryKey: ['sessions'] })
  }, [refetchSessionDetails, store.sessionId])

  const handleFileSelected = async (file: File) => {
    if (!store.sessionId) return
    const tempId = crypto.randomUUID()
    const placeholder: PendingArtifact = {
      artifact_id: tempId,
      filename: file.name,
      mime_type: file.type,
      size_bytes: file.size,
      session_id: store.sessionId,
      uploading: true,
    }
    setPendingArtifacts((prev) => [...prev, placeholder])
    try {
      const result = await files.upload(file, store.sessionId)
      setPendingArtifacts((prev) =>
        prev.map((a) =>
          a.artifact_id === tempId ? { ...result, uploading: false } : a,
        ),
      )
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Upload failed'
      setPendingArtifacts((prev) =>
        prev.map((a) =>
          a.artifact_id === tempId ? { ...a, uploading: false, error: msg } : a,
        ),
      )
    }
  }

  const handleRemoveArtifact = (artifactId: string) => {
    setPendingArtifacts((prev) => prev.filter((a) => a.artifact_id !== artifactId))
  }

  const handleSend = async (message: string, artifactIds: string[]) => {
    if (!store.sessionId) return
    store.clearToolTrace()
    const content =
      message ||
      (artifactIds.length > 0
        ? `[Attached ${artifactIds.length} file${artifactIds.length > 1 ? 's' : ''}]`
        : '')
    const attachedArtifacts: AttachedArtifactRef[] = pendingArtifacts
      .filter(
        (a) =>
          artifactIds.includes(a.artifact_id) && !a.uploading && !a.error,
      )
      .map((a) => ({
        artifact_id: a.artifact_id,
        filename: a.filename,
        mime_type: a.mime_type,
        size_bytes: a.size_bytes,
      }))
    store.addMessage({
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: Date.now(),
      attachedArtifacts:
        attachedArtifacts.length > 0 ? attachedArtifacts : undefined,
    })
    setInput('')
    setPendingArtifacts([])
    try {
      const res = await sessions.sendMessage(store.sessionId, message, artifactIds)
      if (res.ok) {
        await streamResponse(res)
        await onAfterInterrupt()
      } else {
        store.addMessage({
          id: crypto.randomUUID(),
          role: 'error',
          content: `Request failed (${res.status})`,
          timestamp: Date.now(),
        })
        store.setStatus('failed')
      }
    } catch {
      store.addMessage({
        id: crypto.randomUUID(),
        role: 'error',
        content: 'Could not reach the server — check your connection',
        timestamp: Date.now(),
      })
      store.setStatus('failed')
    }
  }

  const handleStop = async () => {
    if (!store.sessionId || store.status !== 'running') return
    abort()
    try {
      await sessions.stop(store.sessionId)
      store.appendSessionLog('Stop requested')
      store.setStatus('idle')
    } catch {
      store.addMessage({
        id: crypto.randomUUID(),
        role: 'error',
        content: 'Could not stop the current execution',
        timestamp: Date.now(),
      })
      store.setStatus('failed')
    }
  }

  const statusInfo = STATUS_LABELS[store.status] ?? STATUS_LABELS.idle
  const sessionTitle = store.messages[0]?.content?.slice(0, 48) ?? 'New Session'

  return (
    <div className="flex h-screen bg-surface-canvas overflow-hidden">
      <Sidebar />
      {isAuthenticated ? <SessionListPanel /> : null}

      <div
        className={cn(
          'flex min-w-0 flex-1 flex-col transition-[margin-left] duration-200 ease-out motion-reduce:transition-none',
          isAuthenticated && sessionSidebarOpen && 'ml-80',
          !isAuthenticated || !sessionSidebarOpen ? 'ml-16' : null,
        )}
      >
        {/* Chat header */}
        <header
          className={cn(
            'flex h-14 shrink-0 items-center border-b border-surface-border bg-surface-base px-5',
            isAuthenticated && !sessionSidebarOpen && 'pl-14',
          )}
        >
          <h1 className="text-[15px] font-semibold text-text-heading truncate flex-1 max-w-[400px]">
            {sessionTitle}
          </h1>
          <div
            className="ml-3 flex items-center h-6 px-2.5 rounded-sm bg-brand-primary-dim border border-[rgba(59,110,248,0.3)] shrink-0"
          >
            <span className={cn('text-[11px] font-medium', statusInfo.color)}>
              {statusInfo.label}
            </span>
          </div>
          <div className="flex-1" />
          <div className="flex items-center gap-2">
            <IntegrationsButton />
            <button
              onClick={store.openCredentialsModal}
              aria-label="Manage credentials"
              className="flex items-center gap-1.5 h-8 px-3 rounded-md bg-surface-overlay border border-surface-borderLight text-[12px] font-medium text-text-body hover:border-surface-muted transition-colors"
            >
              🔑 Credentials
            </button>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto scrollbar-thin px-5 py-5">
          <div className="flex flex-col gap-3 max-w-[calc(100%-8px)]">
            <ul
              className="m-0 flex list-none flex-col gap-3 p-0"
              aria-label="Conversation and execution timeline"
            >
              {chatTimeline.map((item) =>
                item.kind === 'message' ? (
                  <li key={item.msg.id} className="list-none">
                    <MessageBubble message={item.msg} />
                  </li>
                ) : (
                  <ToolTimelineRow key={item.trace.call_id} trace={item.trace} />
                ),
              )}
              {store.status === 'running' && !store.streamingMessageId && (
                <li className="list-none">
                  <StreamingDots />
                </li>
              )}
            </ul>

            {/* Interrupt cards — dispatched by interrupt_type */}
            {store.interrupts.map((interrupt) => (
              <InterruptDispatch
                key={interrupt.interrupt_id}
                interrupt={interrupt}
                sessionId={store.sessionId ?? ''}
                streamResponse={streamResponse}
                onAfterInterrupt={onAfterInterrupt}
              />
            ))}

            <div ref={bottomRef} />
          </div>
        </div>

        {/* Input bar */}
        <div className="px-5 py-4 border-t border-surface-border shrink-0">
          {store.status === 'failed' && (
            <div className="flex items-center gap-2 mb-2">
              <span className="text-[12px] text-semantic-error">Something went wrong.</span>
              <button
                onClick={() => store.setStatus('idle')}
                className="text-[12px] font-medium text-brand-primary-light hover:underline"
              >
                Retry
              </button>
            </div>
          )}
          <InputBar
            value={input}
            onChange={setInput}
            onSubmit={handleSend}
            onStop={handleStop}
            onFileSelected={handleFileSelected}
            pendingArtifacts={pendingArtifacts}
            onRemoveArtifact={handleRemoveArtifact}
            placeholder="Continue the conversation…"
            disabled={store.status === 'running'}
            isRunning={store.status === 'running'}
            size="chat"
          />
        </div>
      </div>

      {/* Right Panel */}
      <RightPanel />

      {/* Modals */}
      <CredentialsModal />
      <SaveWorkflowModal />
      <CrmSetupModal />
      <IntegrationsModal />
    </div>
  )
}

// ── Interrupt dispatcher ───────────────────────────────────────────────────────

interface InterruptDispatchProps {
  interrupt: Interrupt
  sessionId: string
  streamResponse: (res: Response) => Promise<void>
  onAfterInterrupt: () => Promise<void>
}

function InterruptDispatch({
  interrupt,
  sessionId,
  streamResponse,
  onAfterInterrupt,
}: InterruptDispatchProps) {
  const noop = () => { /* dismiss is handled by stream completion */ }

  switch (interrupt.interrupt_type) {
    case 'AUTH_FORM_SUBMISSION':
      return (
        <InterruptCredentialModal
          interrupt={interrupt}
          sessionId={sessionId}
          streamResponse={streamResponse}
          onAfterStream={onAfterInterrupt}
          onDismiss={noop}
        />
      )

    case 'HITL_APPROVAL':
      return (
        <HitlApprovalModal
          interrupt={interrupt}
          sessionId={sessionId}
          streamResponse={streamResponse}
          onAfterStream={onAfterInterrupt}
          onDismiss={noop}
        />
      )

    case 'AUTH_CALLBACK':
    case 'AGENT_OAUTH_CALLBACK':
      return (
        <InlineInterruptCard interrupt={interrupt}>
          <OAuthPopupHandler
            interrupt={interrupt}
            sessionId={sessionId}
            onAfterComplete={onAfterInterrupt}
            onDeny={onAfterInterrupt}
            streamResponse={streamResponse}
          />
        </InlineInterruptCard>
      )

    case 'CRM_SETUP':
      return (
        <AgentInterruptModal
          interrupt={interrupt}
          sessionId={sessionId}
          streamResponse={streamResponse}
          onAfterStream={onAfterInterrupt}
        />
      )

    case 'INSUFFICIENT_CREDITS':
      return (
        <InsufficientCreditsModal interrupt={interrupt} />
      )

    case 'HITL_CLARIFICATION':
    case 'AGENT_CLARIFICATION':
    default:
      return (
        <InlineInterruptCard interrupt={interrupt}>
          <ClarificationInput
            interrupt={interrupt}
            sessionId={sessionId}
            streamResponse={streamResponse}
            onAfterStream={onAfterInterrupt}
          />
        </InlineInterruptCard>
      )
  }
}

// ── Shared inline card wrapper ─────────────────────────────────────────────────

function InlineInterruptCard({
  interrupt,
  children,
}: {
  interrupt: Interrupt
  children: React.ReactNode
}) {
  const title =
    interrupt.interrupt_type === 'AGENT_CLARIFICATION'
      ? 'Agent Input Required'
      : 'Input Required'

  return (
    <div className="mx-0 px-4 py-3 rounded-md bg-semantic-warningDim border border-[#2D2000]">
      <p className="text-label font-medium text-semantic-warning mb-2">⚠ {title}</p>
      {children}
    </div>
  )
}

// ── Insufficient credits modal ─────────────────────────────────────────────────

function InsufficientCreditsModal({ interrupt }: { interrupt: Interrupt }) {
  const [dismissed, setDismissed] = useState(false)
  const meta = interrupt.metadata as Partial<InsufficientCreditsMetadata>
  const reason = meta.reason ?? 'insufficient_credits'
  const amountOwed = meta.amount_owed && meta.amount_owed !== '0' ? meta.amount_owed : null
  const agentName = meta.agent_display_name || 'the agent'

  if (dismissed) return null

  const title = reason === 'arrears' ? 'Account in Arrears' : 'Insufficient Credits'
  const body =
    reason === 'arrears'
      ? `Your account has an outstanding balance${amountOwed ? ` of $${amountOwed}` : ''}. Clear it to continue.`
      : `You don't have enough credits to invoke ${agentName}. Top up to resume.`

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <div
        className="absolute inset-0 bg-surface-canvas/70"
        onClick={() => setDismissed(true)}
        aria-hidden="true"
      />
      <div className="relative w-[420px] flex flex-col bg-surface-elevated border border-surface-border rounded-lg shadow-lg overflow-hidden">
        {/* Header */}
        <div className="flex items-center gap-3 px-5 h-14 border-b border-surface-border">
          <div className="size-9 flex items-center justify-center rounded-md bg-semantic-errorDim text-base">
            💳
          </div>
          <p className="flex-1 text-[15px] font-semibold text-text-heading">{title}</p>
          <button
            onClick={() => setDismissed(true)}
            aria-label="Close"
            className="size-7 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-overlay hover:text-text-body transition-colors"
          >
            ✕
          </button>
        </div>
        {/* Body */}
        <div className="p-5">
          <p className="text-body-md text-text-body">{body}</p>
        </div>
        {/* Footer */}
        <div className="flex items-center gap-2 px-5 py-4 border-t border-surface-border">
          <button
            onClick={() => setDismissed(true)}
            className="flex-1 h-9 rounded-md bg-surface-overlay border border-surface-borderLight text-label text-text-body hover:border-surface-muted transition-colors"
          >
            Close
          </button>
          <a
            href="/settings"
            onClick={() => setDismissed(true)}
            className="flex-1 h-9 flex items-center justify-center rounded-md bg-brand-primary text-white text-label font-medium hover:bg-brand-primary-hover transition-colors"
          >
            Top Up Credits
          </a>
        </div>
      </div>
    </div>
  )
}

// ── Clarification text input (HITL + Agent) ────────────────────────────────────

function ClarificationInput({
  interrupt,
  sessionId,
  streamResponse,
  onAfterStream,
}: {
  interrupt: Interrupt
  sessionId: string
  streamResponse: (res: Response) => Promise<void>
  onAfterStream: () => Promise<void>
}) {
  const meta = interrupt.metadata as Partial<HitlClarificationMetadata & AgentClarificationMetadata>
  const question = meta.question ?? interrupt.message

  const [value, setValue] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async () => {
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
      setError('Could not reach the server — check your connection')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex flex-col gap-2">
      {question && question !== interrupt.message && (
        <p className="text-body-md text-text-body">{question}</p>
      )}
      {!question && (
        <p className="text-body-md text-text-body">{interrupt.message}</p>
      )}
      {error && <p className="text-caption text-semantic-error">{error}</p>}
      <div className="flex gap-2">
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSubmit()}
          placeholder="Your response…"
          aria-label="Clarification response"
          autoFocus
          className="flex-1 h-9 px-3 rounded-md bg-surface-base border border-surface-borderLight text-label text-text-body placeholder:text-text-disabled focus:outline-none focus:border-brand-primary"
        />
        <button
          onClick={handleSubmit}
          disabled={submitting || !value.trim()}
          className="h-9 px-4 rounded-md bg-brand-primary text-white text-label font-medium hover:bg-brand-primary-hover disabled:opacity-50 transition-colors"
        >
          {submitting ? '…' : 'Submit'}
        </button>
      </div>
    </div>
  )
}

// ── Integrations button ────────────────────────────────────────────────────────

const LEAD_GEN_URL = leadGenBaseUrl()

function IntegrationsButton() {
  const sessionId            = useSessionStore((s) => s.sessionId)
  const integrationsOpen     = useSessionStore((s) => s.integrationsModalOpen)
  const openIntegrationsModal = useSessionStore((s) => s.openIntegrationsModal)

  const [connectedCount, setConnectedCount] = useState(0)

  const fetchStatus = useCallback(async () => {
    if (!sessionId) return
    try {
      const res = await fetch(
        `${LEAD_GEN_URL}/tool-settings/status?tenant_id=${encodeURIComponent(sessionId)}`,
      )
      if (!res.ok) return
      const data = await res.json()
      const count = Object.values(data.tools ?? {}).filter(
        (t) => (t as { connected: boolean }).connected,
      ).length
      setConnectedCount(count)
    } catch { /* lead-gen may not be running */ }
  }, [sessionId])

  useEffect(() => { void fetchStatus() }, [fetchStatus])
  useEffect(() => { if (!integrationsOpen) void fetchStatus() }, [integrationsOpen, fetchStatus])

  return (
    <button
      onClick={openIntegrationsModal}
      aria-label="Manage integrations"
      title="Connect tools your agents can use"
      className="relative flex items-center gap-1.5 h-8 px-3 rounded-md bg-surface-overlay border border-surface-borderLight text-[12px] font-medium text-text-body hover:border-surface-muted transition-colors"
    >
      <span>⚡</span>
      <span>Integrations</span>
      {connectedCount > 0 && (
        <span className="flex items-center justify-center size-4 rounded-full bg-semantic-success text-[9px] font-bold text-white leading-none">
          {connectedCount}
        </span>
      )}
    </button>
  )
}
