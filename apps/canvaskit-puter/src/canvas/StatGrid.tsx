import type { StatGridSpec } from '../types/canvas'

const COLS: Record<number, string> = {
  2: 'grid-cols-2',
  3: 'grid-cols-3',
  4: 'grid-cols-4',
}

export function StatGrid({ spec }: { spec: StatGridSpec }) {
  const cols = COLS[spec.columns ?? 3] ?? 'grid-cols-3'
  return (
    <div className={`grid ${cols} gap-3`}>
      {spec.stats.map((stat, i) => {
        const delta = stat.delta
        const trendColor =
          delta == null ? 'text-text-secondary'
          : delta > 0 ? 'text-semantic-success'
          : delta < 0 ? 'text-semantic-error'
          : 'text-text-secondary'
        return (
          <div
            key={i}
            className="flex flex-col gap-1 rounded-xl bg-surface-elevated border border-surface-border px-4 py-3"
          >
            <span className="text-[11px] font-medium uppercase tracking-wide text-text-secondary truncate">
              {stat.label}
            </span>
            <div className="flex items-baseline gap-1.5">
              <span className="text-[22px] font-bold leading-none text-text-heading">
                {typeof stat.value === 'number' ? stat.value.toLocaleString() : stat.value}
              </span>
              {stat.unit && (
                <span className="text-[12px] text-text-secondary">{stat.unit}</span>
              )}
            </div>
            {delta != null && (
              <span className={`text-[12px] font-medium ${trendColor}`}>
                {delta > 0 ? '↑' : '↓'} {Math.abs(delta)}%
              </span>
            )}
          </div>
        )
      })}
    </div>
  )
}
