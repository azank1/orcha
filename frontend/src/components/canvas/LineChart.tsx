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
  const colors = spec.colors ?? DEFAULT_COLORS
  return (
    <div className="rounded-xl bg-surface-elevated border border-surface-border px-5 py-4">
      {spec.title && (
        <p className="mb-3 text-[13px] font-semibold text-text-heading">{spec.title}</p>
      )}
      <ResponsiveContainer width="100%" height={180}>
        <ReLineChart data={spec.data} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
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
          {spec.y_keys.map((key, i) => (
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
