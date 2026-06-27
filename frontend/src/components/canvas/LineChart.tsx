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

const DEFAULT_COLORS = ['#3B6EF8', '#00C8E8', '#A855F7', '#22C55E', '#F59E0B']

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
    DEFAULT_COLORS
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
          <span className="h-2 w-2 rounded-full bg-[#3B6EF8] shrink-0" aria-hidden />
          <p className="text-[13px] font-semibold text-text-heading">{spec.title}</p>
        </div>
      )}
      <ResponsiveContainer width="100%" height={180}>
        <ReLineChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis
            dataKey={spec.x_key}
            tick={{ fill: '#9CA3AF', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: '#9CA3AF', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              background: '#1E2330',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 8,
              fontSize: 12,
            }}
          />
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
