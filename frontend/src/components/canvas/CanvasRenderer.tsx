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
  const isDashboard = manifest.layout === 'dashboard'

  return (
    <div className={`rounded-xl overflow-hidden ${className}`}>
      {manifest.title && (
        <div className="mb-3 flex items-center gap-2">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-text-secondary">
            Canvas
          </span>
          <h3 className="text-[15px] font-semibold text-text-heading">{manifest.title}</h3>
        </div>
      )}
      <div className={GRID_CLASS[manifest.layout]}>
        {manifest.components.map((spec) => (
          <div
            key={spec.id}
            className={isDashboard && isDashboardWide(spec) ? 'col-span-2' : ''}
          >
            <CanvasComponentRenderer spec={spec} />
          </div>
        ))}
      </div>
    </div>
  )
}
