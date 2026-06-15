/**
 * AuthCallback — static page rendered inside the OAuth popup window.
 * The gateway redirects the popup here after agent-callback processing.
 * We immediately close the popup so the main window's poll detects it.
 */
import { useEffect } from 'react'

export function AuthCallback() {
  useEffect(() => {
    // Give the page a tick to render, then close.
    const t = setTimeout(() => window.close(), 100)
    return () => clearTimeout(t)
  }, [])

  return (
    <div className="flex h-screen items-center justify-center bg-surface-canvas">
      <p className="text-body-md text-text-secondary">Authorization complete. Closing…</p>
    </div>
  )
}
