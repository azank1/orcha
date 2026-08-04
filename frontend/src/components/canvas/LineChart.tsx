import {
  ResponsiveContainer,
  LineChart as ReLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts'
import type { LineChartSpec } from '../../types/canvas'
import {
  CHART_COLOR_SEQUENCE,
  CHART_GRID_STROKE,
  CHART_TEXT_SECONDARY,
  CHART_TOOLTIP_STYLE,
} from './chartTokens'

export function LineChart({ spec }: { spec: LineChartSpec }) {
  const raw = spec as LineChartSpec & {
    series?: { key: string; color?: string }[]
  }
  const yKeys =
    raw.y_keys ??
    raw.series?.map((s) => s.key).filter(Boolean) ??
    []
  const colors =
    raw.colors ??
    raw.series?.map((s) => s.color).filter((c): c is string => Boolean(c)) ??
    CHART_COLOR_SEQUENCE
  const data = Array.isArray(raw.data) ? raw.data : []

  if (yKeys.length === 0) {
    return (
      <div className="rounded-xl bg-surface-elevated border border-surface-border px-5 py-4">
        {spec.title && (
          <p className="mb-3 text-[13px] font-semibold text-text-heading">{spec.title}</p>
        )}
        <p className="text-[12px] text-text-secondary">Chart data unavailable.</p>
      </div>
    )
  }

  return (
    <div className="rounded-xl bg-surface-overlay border border-surface-border px-5 py-4 shadow-sm">
      {spec.title && (
        <div className="mb-3 flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-brand-primary shrink-0" aria-hidden />
          <p className="text-[13px] font-semibold text-text-heading">{spec.title}</p>
        </div>
      )}
      <ResponsiveContainer width="100%" height={180}>
        <ReLineChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID_STROKE} />
          <XAxis
            dataKey={spec.x_key}
            tick={{ fill: CHART_TEXT_SECONDARY, fontSize: 11, fontFamily: CHART_TOOLTIP_STYLE.fontFamily }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: CHART_TEXT_SECONDARY, fontSize: 11, fontFamily: CHART_TOOLTIP_STYLE.fontFamily }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
          {yKeys.map((key, i) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={colors[i % colors.length]}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          ))}
        </ReLineChart>
      </ResponsiveContainer>
    </div>
  )
}
