import type { UIManifest, CanvasComponent } from '../../types/canvas'
import { MetricCard } from './MetricCard'
import { LineChart } from './LineChart'
import { DataTable } from './DataTable'
import { AlertFeed } from './AlertFeed'
import { PieChart } from './PieChart'
import { StatGrid } from './StatGrid'
import { ProgressBar } from './ProgressBar'
import { Timeline } from './Timeline'
import { MarkdownCard } from './MarkdownCard'

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
    case 'markdown_card': return <MarkdownCard spec={spec} />
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
    <div className={`overflow-hidden ${className}`}>
      <div className="mb-4 flex items-center gap-3">
        <div className="h-px flex-1 bg-surface-borderLight" />
        <span className="shrink-0 text-[10px] font-semibold uppercase tracking-widest text-text-disabled">
          {manifest.title ?? 'Dashboard'}
        </span>
        {isDemoManifest(manifest) && (
          <span className="shrink-0 rounded-full border border-surface-borderLight bg-surface-base px-2 py-0.5 text-[10px] text-text-disabled">
            Demo data
          </span>
        )}
        <div className="h-px flex-1 bg-surface-borderLight" />
      </div>
      <div className={GRID_CLASS[layout] ?? GRID_CLASS.dashboard}>
        {components.map((spec, i) => (
          <div
            key={spec.id ?? `${spec.type}-${i}`}
            className={`animate-canvas-enter ${isDashboard && isDashboardWide(spec) ? 'col-span-2' : ''}`}
            style={{ animationDelay: `${i * 180}ms`, opacity: 0, animationFillMode: 'forwards' }}
          >
            <CanvasComponentRenderer spec={spec} />
          </div>
        ))}
      </div>
    </div>
  )
}
