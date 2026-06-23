import type { UIManifest, CanvasComponent } from '../../types/canvas'
import { MetricCard } from './MetricCard'
import { LineChart } from './LineChart'
import { DataTable } from './DataTable'
import { AlertFeed } from './AlertFeed'
import { PieChart } from './PieChart'
import { StatGrid } from './StatGrid'
import { ProgressBar } from './ProgressBar'
import { Timeline } from './Timeline'

function CanvasComponentRenderer({ spec }: { spec: CanvasComponent }) {
  switch (spec.type) {
    case 'metric_card':  return <MetricCard spec={spec} />
    case 'line_chart':   return <LineChart spec={spec} />
    case 'data_table':   return <DataTable spec={spec} />
    case 'alert_feed':   return <AlertFeed spec={spec} />
    case 'pie_chart':    return <PieChart spec={spec} />
    case 'stat_grid':    return <StatGrid spec={spec} />
    case 'progress_bar': return <ProgressBar spec={spec} />
    case 'timeline':     return <Timeline spec={spec} />
    default:             return null
  }
}

const SANDBOX_MODE = import.meta.env.VITE_SANDBOX_MODE === 'true'

function isDemoManifest(manifest: UIManifest): boolean {
  if (SANDBOX_MODE) return true
  const title = manifest.title?.toLowerCase() ?? ''
  return title.includes('sample data') || title.includes('demo')
}

const GRID_CLASS: Record<UIManifest['layout'], string> = {
  dashboard: 'grid grid-cols-2 gap-4',
  single:    'flex flex-col gap-4',
  table:     'flex flex-col gap-4',
  timeline:  'flex flex-col gap-4',
}

// Dashboard layout: single-column components get full width
function isDashboardWide(spec: CanvasComponent): boolean {
  return (
    spec.type === 'line_chart' ||
    spec.type === 'data_table' ||
    spec.type === 'alert_feed' ||
    spec.type === 'timeline' ||
    spec.type === 'stat_grid'
  )
}

export function CanvasRenderer({
  manifest,
  className = '',
}: {
  manifest: UIManifest
  className?: string
}) {
  const layout = manifest.layout ?? 'dashboard'
  const components = Array.isArray(manifest.components) ? manifest.components : []
  const isDashboard = layout === 'dashboard'

  return (
    <div className={`rounded-xl overflow-hidden ${className}`}>
      {manifest.title && (
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-text-secondary">
            Canvas
          </span>
          <h3 className="text-[15px] font-semibold text-text-heading">{manifest.title}</h3>
          {isDemoManifest(manifest) && (
            <span className="rounded-full border border-surface-borderLight bg-surface-overlay px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-text-secondary">
              Demo data — not connected to your accounts
            </span>
          )}
        </div>
      )}
      <div className={GRID_CLASS[layout] ?? GRID_CLASS.dashboard}>
        {components.map((spec, i) => (
          <div
            key={spec.id ?? `${spec.type}-${i}`}
            className={isDashboard && isDashboardWide(spec) ? 'col-span-2' : ''}
          >
            <CanvasComponentRenderer spec={spec} />
          </div>
        ))}
      </div>
    </div>
  )
}
