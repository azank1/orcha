/**
 * OAuthPopupHandler — renders an inline prompt for AUTH_CALLBACK / AGENT_OAUTH_CALLBACK
 * interrupts. Opens the OAuth consent URL in a popup window and polls until
 * the popup closes, then triggers a session status refresh.
 *
 * NOTE: Do NOT pass noopener/noreferrer to window.open() — those flags cause modern
 * browsers to return null even when the popup actually opens, making us falsely
 * report "Popup was blocked" and preventing resume-polling from starting.
 */
import { useEffect, useRef, useState } from 'react'
import type { AgentOAuthCallbackMetadata, AuthCallbackMetadata, Interrupt } from '../../types'
import { sessions } from '../../api/client'
import { Button } from '../ui/Button'

interface Props {
  interrupt: Interrupt
  sessionId: string
  onAfterComplete: () => Promise<void>
  onDeny: () => Promise<void>
  streamResponse: (res: Response) => Promise<void>
}

export function OAuthPopupHandler({ interrupt, sessionId, onAfterComplete, onDeny, streamResponse }: Props) {
  const meta = interrupt.metadata as Partial<AuthCallbackMetadata & AgentOAuthCallbackMetadata>
  const [opened, setOpened] = useState(false)
  const [waitingClose, setWaitingClose] = useState(false)
  const [denying, setDenying] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [resuming, setResuming] = useState(false)
  const popupRef = useRef<Window | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const authUrl = meta.auth_url ?? ''
  const providerName = meta.provider_name ?? 'OAuth Provider'
  const scopes = meta.scopes ?? []

  // Stop polling on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current != null) clearInterval(pollRef.current)
    }
  }, [])

  const sendResume = () => {
    if (pollRef.current != null) clearInterval(pollRef.current)
    setWaitingClose(false)
    setResuming(true)
    sessions
      .resume(sessionId, interrupt.interrupt_id, interrupt.interrupt_type, { status: 'granted' })
      .then((res) => {
        if (res.ok) return streamResponse(res)
      })
      .then(() => onAfterComplete())
      .catch(() => setResuming(false))
  }

  const openPopup = () => {
    if (!authUrl) return
    setError(null)

    // Do NOT include noopener/noreferrer — they cause window.open() to return null
    // in modern browsers even when the popup successfully opens, which breaks
    // both the blocked-popup detection and the close-polling.
    const popup = window.open(
      authUrl,
      'emerge_oauth',
      'width=600,height=720,left=200,top=100',
    )

    if (!popup) {
      // Truly blocked by the browser
      setError('blocked')
      return
    }

    popupRef.current = popup
    setOpened(true)
    setWaitingClose(true)

    pollRef.current = setInterval(() => {
      try {
        if (popup.closed) {
          sendResume()
        }
      } catch {
        // Cross-origin access error — ignore and keep polling
      }
    }, 500)
  }

  const handleDeny = async () => {
    if (pollRef.current != null) clearInterval(pollRef.current)
    setDenying(true)
    try {
      const res = await sessions.resume(
        sessionId,
        interrupt.interrupt_id,
        interrupt.interrupt_type,
        { status: 'denied' },
      )
      if (res.ok) await onDeny()
    } catch { /* ignore */ }
    setDenying(false)
  }

  return (
    <div className="flex flex-col gap-3">
      <p className="text-body-md text-text-body">{interrupt.message}</p>
      {scopes.length > 0 && (
        <p className="text-caption text-text-secondary">
          <span className="font-medium">Requested scopes:</span> {scopes.join(', ')}
        </p>
      )}

      {error === 'blocked' && (
        <div className="flex flex-col gap-1.5">
          <p className="text-caption text-semantic-error">
            Popup was blocked by your browser.{' '}
            <a
              href={authUrl}
              target="_blank"
              rel="noreferrer"
              className="underline hover:no-underline"
            >
              Open authorization page in a new tab
            </a>
            , then click the button below once you've authorized.
          </p>
        </div>
      )}

      {waitingClose ? (
        <div className="flex flex-col gap-2">
          <p className="text-caption text-text-secondary italic animate-pulse">
            Waiting for authorization window to close…
          </p>
          <p className="text-caption text-text-secondary">
            Authorized already?{' '}
            <button
              onClick={sendResume}
              disabled={resuming}
              className="underline hover:no-underline disabled:opacity-50"
            >
              {resuming ? 'Resuming…' : 'Click here to continue'}
            </button>
          </p>
        </div>
      ) : (
        <div className="flex gap-2 flex-wrap">
          <Button size="sm" onClick={openPopup} disabled={!authUrl || resuming}>
            {opened ? `Reopen ${providerName}` : `Connect to ${providerName}`}
          </Button>
          {(error === 'blocked' || opened) && (
            <Button
              size="sm"
              onClick={sendResume}
              disabled={resuming}
              className="bg-surface-overlay border border-surface-borderLight text-text-body hover:border-surface-muted"
            >
              {resuming ? 'Resuming…' : "I've authorized — continue"}
            </Button>
          )}
          <Button
            size="sm"
            onClick={handleDeny}
            loading={denying}
            className="bg-surface-overlay border border-surface-borderLight text-text-body hover:border-surface-muted"
          >
            Deny
          </Button>
        </div>
      )}
    </div>
  )
}
