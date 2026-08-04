import type { TimelineSpec } from '../../types/canvas'

const STATUS_STYLES = {
  complete: { dot: 'bg-semantic-success border-semantic-success', line: 'bg-semantic-success/30', label: 'text-text-body' },
  active:   { dot: 'bg-brand-primary border-brand-primary ring-2 ring-brand-primary/30', line: 'bg-surface-border', label: 'text-text-heading font-medium' },
  pending:  { dot: 'bg-surface-overlay border-surface-muted', line: 'bg-surface-border', label: 'text-text-secondary' },
} as const

export function Timeline({ spec }: { spec: TimelineSpec }) {
  return (
    <div className="rounded-xl bg-surface-elevated border border-surface-border px-5 py-4">
      {spec.title && (
        <p className="mb-4 text-[13px] font-semibold text-text-heading">{spec.title}</p>
      )}
      <ol className="relative ml-3 flex flex-col gap-0">
        {spec.events.map((ev, i) => {
          const status = ev.status ?? 'pending'
          const s = STATUS_STYLES[status]
          const isLast = i === spec.events.length - 1
          return (
            <li key={ev.id} className="relative flex gap-4 pb-5 last:pb-0">
              {/* connector line */}
              {!isLast && (
                <span
                  className={`absolute left-[7px] top-4 h-full w-px ${s.line}`}
                  aria-hidden
                />
              )}
              {/* dot */}
              <span
                className={`relative z-10 mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border ${s.dot}`}
              />
              <div className="flex-1 min-w-0">
                <p className={`text-[13px] ${s.label}`}>{ev.label}</p>
                {ev.description && (
                  <p className="mt-0.5 text-[12px] text-text-secondary">{ev.description}</p>
                )}
                {ev.timestamp && (
                  <p className="mt-0.5 text-[11px] font-mono text-text-secondary">{ev.timestamp}</p>
                )}
              </div>
            </li>
          )
        })}
      </ol>
    </div>
  )
}
