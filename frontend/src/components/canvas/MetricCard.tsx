import type { MetricCardSpec } from '../../types/canvas'

function TrendArrow({ trend, delta }: { trend?: 'up' | 'down' | 'flat'; delta?: number }) {
  if (!trend || trend === 'flat') return null
  const isUp = trend === 'up'
  const color = isUp ? 'text-semantic-success' : 'text-semantic-error'
  const arrow = isUp ? '↑' : '↓'
  return (
    <span className={`text-label font-mono ${color}`}>
      {arrow} {delta != null ? `${Math.abs(delta)}%` : ''}
    </span>
  )
}

export function MetricCard({ spec }: { spec: MetricCardSpec }) {
  const accentColor =
    spec.trend === 'up'
      ? 'border-l-semantic-success'
      : spec.trend === 'down'
        ? 'border-l-semantic-error'
        : 'border-l-brand-primary'

  return (
    <div className={`flex flex-col gap-1.5 rounded-xl bg-surface-overlay border border-surface-border border-l-[3px] ${accentColor} px-5 py-4 shadow-sm`}>
      <span className="text-[10px] font-semibold uppercase tracking-widest text-text-secondary">
        {spec.label}
      </span>
      <div className="flex items-baseline gap-2">
        <span className="text-[30px] font-mono font-bold leading-none tracking-tight text-text-heading">
          {spec.value == null
            ? '—'
            : typeof spec.value === 'number'
              ? spec.value.toLocaleString()
              : spec.value}
        </span>
        {spec.unit && (
          <span className="text-mono font-mono text-text-secondary">{spec.unit}</span>
        )}
      </div>
      {(spec.trend || spec.sub_label) && (
        <div className="flex items-center gap-2">
          <TrendArrow trend={spec.trend} delta={spec.delta} />
          {spec.sub_label && (
            <span className="text-[12px] text-text-secondary">{spec.sub_label}</span>
          )}
        </div>
      )}
    </div>
  )
}
