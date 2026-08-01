import {
  ResponsiveContainer,
  PieChart as RePieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from 'recharts'
import type { PieChartSpec } from '../../types/canvas'
import { CHART_COLOR_SEQUENCE, CHART_MONO_FONT_STACK, CHART_TOOLTIP_STYLE } from './chartTokens'

export function PieChart({ spec }: { spec: PieChartSpec }) {
  const data = spec.data.map((d, i) => ({
    ...d,
    color: d.color ?? CHART_COLOR_SEQUENCE[i % CHART_COLOR_SEQUENCE.length],
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
            contentStyle={CHART_TOOLTIP_STYLE}
            formatter={(value: number) => [
              `${value.toLocaleString()} (${((value / data.reduce((s, d) => s + d.value, 0)) * 100).toFixed(1)}%)`,
            ]}
          />
          <Legend
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize: 12, color: '#9CA3AF', fontFamily: CHART_MONO_FONT_STACK }}
          />
        </RePieChart>
      </ResponsiveContainer>
    </div>
  )
}
