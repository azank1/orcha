import { useEffect, useRef, useState } from 'react'
import { useSessionStore } from '../../store/session'
import { cn } from '../ui/cn'

function eventClass(type: string): string {
  if (type === 'error') return 'text-semantic-error'
  if (type === 'interrupt') return 'text-semantic-warning'
  if (type === 'invocation_result' || type === 'done') return 'text-text-body'
  return 'text-text-secondary'
}

/**
 * Live SSE event log for the active run. Reads the session store's
 * traceBuffer, which useSSE fills from the single active stream — no second
 * connection is opened here.
 */
export function TraceTab() {
  const traceBuffer = useSessionStore((s) => s.traceBuffer)
  const [paused, setPaused] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!paused) bottomRef.current?.scrollIntoView({ behavior: 'auto' })
  }, [traceBuffer.length, paused])

  return (
    <div className="px-3">
      <div className="flex items-center justify-between mb-2 px-1">
        <p className="text-[10px] font-semibold text-text-disabled tracking-caps uppercase">
          SSE Trace
        </p>
        <span className="font-mono text-[10px] text-text-disabled">
          {paused ? 'paused' : `${traceBuffer.length} events`}
        </span>
      </div>

      {traceBuffer.length === 0 ? (
        <p className="px-1 font-mono text-caption text-text-disabled">
          No events yet — send a message to start a run.
        </p>
      ) : (
        <div
          onMouseEnter={() => setPaused(true)}
          onMouseLeave={() => setPaused(false)}
          className="max-h-[60vh] overflow-y-auto scrollbar-thin rounded-md border border-surface-border bg-surface-base px-2.5 py-2"
          aria-label="Live SSE event log"
        >
          <ul className="m-0 flex list-none flex-col gap-1 p-0">
            {traceBuffer.map((e) => (
              <li key={e.id} className="font-mono text-[10px] leading-4">
                <span className="text-text-disabled">
                  {new Date(e.timestamp).toLocaleTimeString(undefined, {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                  })}
                </span>{' '}
                <span className={cn(eventClass(e.type))}>{e.type}</span>
              </li>
            ))}
          </ul>
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  )
}
