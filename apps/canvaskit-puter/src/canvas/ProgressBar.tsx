import type { ProgressBarSpec } from '../types/canvas'

const COLOR_MAP = {
  default: 'bg-brand-primary',
  success: 'bg-semantic-success',
  warning: 'bg-semantic-warning',
  error:   'bg-semantic-error',
} as const

export function ProgressBar({ spec }: { spec: ProgressBarSpec }) {
  const max = spec.max ?? 100
  const pct = Math.min(100, Math.max(0, (spec.value / max) * 100))
  const barColor = COLOR_MAP[spec.color ?? 'default']

  return (
    <div className="rounded-xl bg-surface-elevated border border-surface-border px-5 py-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[13px] font-medium text-text-body">{spec.label}</span>
        <span className="text-[13px] font-semibold text-text-heading">{pct.toFixed(0)}%</span>
      </div>
      <div className="h-2 w-full rounded-full bg-surface-overlay">
        <div
          className={`h-2 rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
