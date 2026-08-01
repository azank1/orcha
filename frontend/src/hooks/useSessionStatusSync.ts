import { useCallback, useEffect } from 'react'
import { sessions } from '../api/client'
import { useSessionStore } from '../store/session'

const POLL_MS = 5000

/**
 * Keeps Session Details (agents, checklist, artifacts, interrupts, token estimate)
 * in sync with GET /api/v1/sessions/:id/status.
 */
export function useSessionStatusSync() {
  const sessionId = useSessionStore((s) => s.sessionId)
  const hydrate = useSessionStore((s) => s.hydrateFromSessionStatus)

  const refetchSessionDetails = useCallback(async () => {
    const sid = useSessionStore.getState().sessionId
    if (!sid) return
    try {
      const data = await sessions.getStatus(sid)
      hydrate(data)
    } catch {
      // Leave existing panel state on error
    }
  }, [hydrate])

  useEffect(() => {
    if (!sessionId) return
    void refetchSessionDetails()
  }, [sessionId, refetchSessionDetails])

  useEffect(() => {
    if (!sessionId) return
    const id = globalThis.setInterval(() => {
      if (document.visibilityState !== 'visible') return
      void refetchSessionDetails()
    }, POLL_MS)
    return () => globalThis.clearInterval(id)
  }, [sessionId, refetchSessionDetails])

  return { refetchSessionDetails }
}
