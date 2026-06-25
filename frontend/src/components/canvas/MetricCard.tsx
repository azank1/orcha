import type { MetricCardSpec } from '../../types/canvas'

function TrendArrow({ trend, delta }: { trend?: 'up' | 'down' | 'flat'; delta?: number }) {
  if (!trend || trend === 'flat') return null
  const isUp = trend === 'up'
  const color = isUp ? 'text-semantic-success' : 'text-semantic-error'
  const arrow = isUp ? '↑' : '↓'
  return (
    <span className={`text-[13px] font-medium ${color}`}>
      {arrow} {delta != null ? `${Math.abs(delta)}%` : ''}
    </span>
  )
}

export function MetricCard({ spec }: { spec: MetricCardSpec }) {
  return (
    <div className="flex flex-col gap-1.5 rounded-xl bg-surface-elevated border border-surface-border px-5 py-4">
      <span className="text-[11px] font-medium uppercase tracking-wide text-text-secondary">
        {spec.label}
      </span>
      <div className="flex items-baseline gap-2">
        <span className="text-[28px] font-bold leading-none text-text-heading">
          {spec.value == null
            ? '—'
            : typeof spec.value === 'number'
              ? spec.value.toLocaleString()
              : spec.value}
        </span>
        {spec.unit && (
          <span className="text-[13px] text-text-secondary">{spec.unit}</span>
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
