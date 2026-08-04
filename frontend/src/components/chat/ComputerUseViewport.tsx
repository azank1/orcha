import { useEffect, useMemo, useRef, useState } from 'react'
import type { ToolInvocationTrace } from '../../types'
import { files, getAccessToken } from '../../api/client'
import { useSessionStore } from '../../store/session'
import { computerUseFrames } from '../../lib/computerUse'
import { cn } from '../ui/cn'

function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(
    () => window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  )
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    const onChange = () => setReduced(mq.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])
  return reduced
}

/**
 * Inline computer-use monitor: plays the step's captured screenshot frames
 * (session artifacts named computer-use-step-N.png) as a ~1 fps flipbook.
 * Loops while the step runs, settles on the last frame when it finishes.
 * Frames are fetched through the authenticated files API and shown as object
 * URLs; before any frame lands, a static placeholder monitor is shown.
 */
export function ComputerUseViewport({ trace }: { readonly trace: ToolInvocationTrace }) {
  const artifacts = useSessionStore((s) => s.artifacts)
  const frames = useMemo(() => computerUseFrames(artifacts), [artifacts])
  const reducedMotion = usePrefersReducedMotion()

  const [urls, setUrls] = useState<Record<string, string>>({})
  const createdUrlsRef = useRef<string[]>([])

  // Fetch any frames we don't have an object URL for yet (auth required).
  useEffect(() => {
    const missing = frames.filter((f) => !urls[f.artifact_id])
    if (missing.length === 0) return
    let cancelled = false
    void (async () => {
      const token = getAccessToken()
      const next: Record<string, string> = {}
      for (const f of missing) {
        try {
          const res = await fetch(files.download(f.artifact_id), {
            headers: token ? { Authorization: `Bearer ${token}` } : {},
          })
          if (!res.ok) continue
          const blob = await res.blob()
          const url = URL.createObjectURL(blob)
          createdUrlsRef.current.push(url)
          next[f.artifact_id] = url
        } catch {
          // best-effort — the placeholder stays until a frame loads
        }
      }
      if (!cancelled && Object.keys(next).length > 0) {
        setUrls((prev) => ({ ...prev, ...next }))
      }
    })()
    return () => {
      cancelled = true
    }
  }, [frames, urls])

  // Revoke object URLs on unmount.
  useEffect(
    () => () => {
      for (const url of createdUrlsRef.current) URL.revokeObjectURL(url)
    },
    [],
  )

  const loaded = frames.filter((f) => urls[f.artifact_id])
  const running = trace.phase === 'running'

  // Flipbook ticker — only advances while the step runs. When settled (or
  // reduced motion), the displayed frame derives to the last captured frame,
  // so no state needs to be set from an effect.
  const [tick, setTick] = useState(0)
  useEffect(() => {
    if (!running || reducedMotion || loaded.length < 2) return
    const t = setInterval(() => setTick((i) => i + 1), 1000)
    return () => clearInterval(t)
  }, [loaded.length, running, reducedMotion])

  const displayedIdx =
    loaded.length === 0
      ? -1
      : running && !reducedMotion
        ? tick % loaded.length
        : loaded.length - 1
  const current = displayedIdx >= 0 ? loaded[displayedIdx] : null

  return (
    <div
      className="mt-2 rounded-lg border border-surface-border bg-[#0b0d12] p-2"
      aria-label="Computer-use viewport"
    >
      {/* Screen */}
      <div className="relative aspect-[16/10] w-full overflow-hidden rounded-md bg-black">
        {current ? (
          <img
            src={urls[current.artifact_id]}
            alt={`Computer-use screenshot, step ${current.step}`}
            className="absolute inset-0 size-full object-contain"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="font-mono text-[11px] text-text-disabled">
              <span className="cu-waiting-pulse">●</span> waiting for frames
            </p>
          </div>
        )}
      </div>

      {/* Status bar */}
      <div className="mt-1.5 flex items-center justify-between px-1">
        <span className="font-mono text-[10px] text-text-disabled">computer_use</span>
        <span
          className={cn(
            'font-mono text-[10px]',
            running ? 'text-brand-primary-light' : 'text-text-disabled',
          )}
        >
          {loaded.length > 0
            ? `frame ${displayedIdx + 1}/${loaded.length}`
            : running
              ? 'capturing…'
              : 'no frames'}
        </span>
      </div>
    </div>
  )
}
