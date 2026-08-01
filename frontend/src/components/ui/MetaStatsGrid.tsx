import { cn } from './cn'

interface MetaStat {
  label: string
  value: string
}

interface MetaStatsGridProps {
  stats: MetaStat[]
  className?: string
}

export function MetaStatsGrid({ stats, className }: MetaStatsGridProps) {
  const items = stats.slice(0, 4)

  return (
    <div
      className={cn(
        'grid grid-cols-2 grid-rows-2 rounded-md bg-surface-overlay border border-surface-border',
        className,
      )}
    >
      {items.map((stat, i) => (
        <div
          key={stat.label}
          className={cn(
            'flex flex-col justify-center px-3 py-2',
            i % 2 === 0 && i < 2 && 'border-r border-surface-border',
            i < 2 && 'border-b border-surface-border',
          )}
        >
          <span className="text-[11px] text-text-disabled leading-none">{stat.label}</span>
          <span className="mt-[6px] text-label font-semibold text-text-body">{stat.value}</span>
        </div>
      ))}
    </div>
  )
}
