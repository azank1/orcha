/**
 * InterruptCredentialModal — shown when an AUTH_FORM_SUBMISSION interrupt fires.
 *
 * The user pastes an API key / bearer token. On submit:
 *   1. POSTs the credential to the vault via sessions.resume with status "complete".
 *   2. Streams the resumed SSE response.
 */
import { useState } from 'react'
import type { AuthFormSubmissionMetadata, Interrupt } from '../../types'
import { sessions } from '../../api/client'
import { Button } from '../ui/Button'

interface Props {
  interrupt: Interrupt
  sessionId: string
  streamResponse: (res: Response) => Promise<void>
  onAfterStream: () => Promise<void>
  onDismiss: () => void
}

export function InterruptCredentialModal({
  interrupt,
  sessionId,
  streamResponse,
  onAfterStream,
  onDismiss,
}: Props) {
  const meta = interrupt.metadata as Partial<AuthFormSubmissionMetadata>
  const [value, setValue] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const formTitle = meta.form_title ?? 'Credential Required'
  const fieldLabel = meta.field_label ?? 'API Key'
  const isSecret = meta.is_secret !== false
  const agentName = meta.agent_display_name ?? null

  const handleSubmit = async () => {
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
      setError('Could not reach the server — check your connection')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeny = async () => {
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
    onDismiss()
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-label={formTitle}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-surface-canvas/70" onClick={handleDeny} aria-hidden="true" />

      <div className="relative w-[420px] flex flex-col bg-surface-elevated border border-surface-border rounded-lg shadow-lg overflow-hidden">
        {/* Header */}
        <div className="flex items-center gap-3 px-5 h-14 border-b border-surface-border">
          <div className="size-9 flex items-center justify-center rounded-md bg-semantic-warningDim text-base">
            🔐
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[15px] font-semibold text-text-heading leading-none">{formTitle}</p>
            {agentName && (
              <p className="text-caption text-text-secondary mt-0.5">{agentName}</p>
            )}
          </div>
        </div>

        {/* Body */}
        <div className="p-5 flex flex-col gap-4">
          <p className="text-body-md text-text-body">{interrupt.message}</p>
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="interrupt-credential-input"
              className="text-label font-medium text-text-heading"
            >
              {fieldLabel}
            </label>
            <input
              id="interrupt-credential-input"
              type={isSecret ? 'password' : 'text'}
              value={value}
              onChange={(e) => setValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
              placeholder="Paste value…"
              autoFocus
              className="h-10 px-3 rounded-md bg-surface-base border border-surface-borderLight text-label text-text-body placeholder:text-text-disabled focus:outline-none focus:border-brand-primary"
            />
          </div>
          {error && (
            <p className="text-caption text-semantic-error">{error}</p>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center gap-2 px-5 py-4 border-t border-surface-border">
          <Button
            size="sm"
            onClick={handleDeny}
            disabled={submitting}
            className="flex-1 bg-surface-overlay border border-surface-borderLight text-text-body hover:border-surface-muted"
          >
            Deny
          </Button>
          <Button
            size="sm"
            onClick={handleSubmit}
            loading={submitting}
            disabled={!value.trim()}
            className="flex-1"
          >
            Submit
          </Button>
        </div>
      </div>
    </div>
  )
}
