import {
  ResponsiveContainer,
  PieChart as RePieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from 'recharts'
import type { PieChartSpec } from '../../types/canvas'

const DEFAULT_COLORS = ['#3B6EF8', '#00C8E8', '#A855F7', '#22C55E', '#F59E0B', '#EF4444']

export function PieChart({ spec }: { spec: PieChartSpec }) {
  const data = spec.data.map((d, i) => ({
    ...d,
    color: d.color ?? DEFAULT_COLORS[i % DEFAULT_COLORS.length],
  }))

  return (
    <div className="rounded-xl bg-surface-elevated border border-surface-border px-5 py-4">
      {spec.title && (
        <p className="mb-3 text-[13px] font-semibold text-text-heading">{spec.title}</p>
      )}
      <ResponsiveContainer width="100%" height={200}>
        <RePieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={80}
            paddingAngle={2}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={index} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: '#1E2330',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 8,
              fontSize: 12,
            }}
            formatter={(value: number) => [
              `${value.toLocaleString()} (${((value / data.reduce((s, d) => s + d.value, 0)) * 100).toFixed(1)}%)`,
            ]}
          />
          <Legend
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize: 12, color: '#9CA3AF' }}
          />
        </RePieChart>
      </ResponsiveContainer>
    </div>
  )
}
