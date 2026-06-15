import { useEffect, useRef, useState } from 'react'
import type { ToolInvocationPhase, ToolInvocationTrace } from '../../types'
import { cn } from '../ui/cn'

interface ToolRunCardProps {
  readonly trace: ToolInvocationTrace
}

function phaseLabel(phase: ToolInvocationPhase): string {
  if (phase === 'running') return 'Running'
  if (phase === 'error') return 'Failed'
  return 'Done'
}

function phaseBadgeClass(phase: ToolInvocationPhase): string {
  if (phase === 'running') {
    return 'bg-brand-primary-dim text-brand-primary-light border-blue-500/30'
  }
  if (phase === 'error') {
    return 'bg-semantic-errorDim text-semantic-error border-semantic-error/30'
  }
  return 'bg-semantic-successDim text-semantic-success border-semantic-success/30'
}

const preScrollableClass =
  'max-h-40 min-h-0 overflow-auto overscroll-contain whitespace-pre-wrap break-words rounded-sm bg-surface-base p-2 font-mono text-caption'

export function ToolRunCard({ trace }: ToolRunCardProps) {
  const wasRunning = useRef(trace.phase === 'running')
  const [open, setOpen] = useState(trace.phase === 'running')

  useEffect(() => {
    if (wasRunning.current && trace.phase !== 'running') {
      setOpen(false)
    }
    wasRunning.current = trace.phase === 'running'
  }, [trace.phase])

  const statusLabel = phaseLabel(trace.phase)
  const statusClass = phaseBadgeClass(trace.phase)

  return (
    <div className="rounded-md border border-surface-border bg-surface-overlay text-body-md">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-label={`${trace.tool_name} invocation, ${statusLabel}. Toggle details.`}
        className="flex w-full flex-wrap items-center gap-2 px-3 py-2 text-left text-label font-medium text-text-body hover:bg-surface-elevated rounded-md transition-colors"
      >
        <span
          className={cn(
            'shrink-0 rounded-sm border px-2 py-0.5 text-caption font-semibold uppercase tracking-wide',
            statusClass,
          )}
        >
          {statusLabel}
        </span>
        <span className="min-w-0 flex-1 truncate font-mono text-caption text-text-secondary">
          {trace.tool_name}
        </span>
        <span className="text-caption text-text-secondary">{trace.agent_id}</span>
        {trace.total_cost_usd && trace.total_cost_usd !== '0' && (
          <span className="shrink-0 rounded-sm border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-caption font-semibold text-amber-400">
            ${parseFloat(trace.total_cost_usd).toFixed(6)}
          </span>
        )}
        <span className="ml-auto text-caption text-text-secondary" aria-hidden>
          {open ? '▼' : '▶'}
        </span>
      </button>
      {open && (
        <div className="border-t border-surface-border px-3 py-2 space-y-2">
          {trace.total_cost_usd && trace.total_cost_usd !== '0' && (
            <div className="flex items-center gap-3 text-caption text-text-secondary">
              <span>
                <span className="font-medium text-text-body">Total cost:</span>{' '}
                <span className="font-mono text-amber-400">${parseFloat(trace.total_cost_usd).toFixed(6)}</span>
              </span>
              {trace.base_fee && trace.base_fee !== '0' && (
                <span className="text-text-secondary/60">
                  (agent fee: ${parseFloat(trace.base_fee).toFixed(6)})
                </span>
              )}
            </div>
          )}
          {trace.progressLines.length > 0 && (
            <ul className="list-disc space-y-1 pl-4 text-caption text-text-secondary">
              {trace.progressLines.map((line, i) => (
                <li key={`${trace.call_id}-p-${i}`}>{line}</li>
              ))}
            </ul>
          )}
          {Object.keys(trace.inputs).length > 0 && (
            <div className="min-h-0">
              <p className="mb-1 text-caption font-medium text-text-secondary">Query</p>
              <pre className={cn(preScrollableClass, 'text-text-secondary')}>
                {JSON.stringify(trace.inputs, null, 2)}
              </pre>
            </div>
          )}
          {trace.content_preview ? (
            <div className="min-h-0">
              <p className="mb-1 text-caption font-medium text-text-secondary">Result</p>
              <pre className={cn(preScrollableClass, 'text-text-body')}>
                {trace.content_preview}
              </pre>
            </div>
          ) : null}
        </div>
      )}
    </div>
  )
}
