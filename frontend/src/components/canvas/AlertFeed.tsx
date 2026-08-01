import type { AlertFeedSpec } from '../../types/canvas'

const SEVERITY_STYLES = {
  info:    { dot: 'bg-semantic-info',    text: 'text-semantic-info',    bg: 'bg-semantic-info/10',    border: 'border-l-2 border-l-semantic-info' },
  warning: { dot: 'bg-semantic-warning', text: 'text-semantic-warning', bg: 'bg-semantic-warning/10', border: 'border-l-2 border-l-semantic-warning' },
  error:   { dot: 'bg-semantic-error',   text: 'text-semantic-error',   bg: 'bg-semantic-error/10',   border: 'border-l-2 border-l-semantic-error' },
  success: { dot: 'bg-semantic-success', text: 'text-semantic-success', bg: 'bg-semantic-success/10', border: 'border-l-2 border-l-semantic-success' },
} as const

export function AlertFeed({ spec }: { spec: AlertFeedSpec }) {
  const raw = spec as AlertFeedSpec & { items?: AlertFeedSpec['alerts'] }
  const alerts = raw.alerts ?? raw.items ?? []

  return (
    <div className="rounded-xl bg-surface-overlay border border-surface-border overflow-hidden shadow-sm">
      {spec.title && (
        <div className="px-5 py-3 border-b border-surface-border bg-surface-elevated/60 flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-semantic-warning shrink-0" aria-hidden />
          <p className="text-[13px] font-semibold text-text-heading">{spec.title}</p>
        </div>
      )}
      <ul className="divide-y divide-surface-border">
        {alerts.map((alert, i) => {
          const s = SEVERITY_STYLES[alert.severity] ?? SEVERITY_STYLES.info
          return (
            <li key={alert.id ?? `alert-${i}`} className={`flex items-start gap-3 px-4 py-3 ${s.bg} ${s.border}`}>
              <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${s.dot}`} />
              <div className="min-w-0 flex-1">
                <p className={`text-[13px] font-medium ${s.text}`}>{alert.title}</p>
                {alert.body && (
                  <p className="mt-0.5 text-[12px] text-text-secondary">{alert.body}</p>
                )}
              </div>
              {alert.timestamp && (
                <span className="shrink-0 text-[11px] font-mono text-text-secondary">{alert.timestamp}</span>
              )}
            </li>
          )
        })}
      </ul>
    </div>
  )
}
