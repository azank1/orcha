import type { DataTableSpec } from '../../types/canvas'

function formatCell(value: unknown, type?: DataTableSpec['columns'][0]['type']): string {
  if (value == null) return '—'
  if (type === 'currency') {
    const n = Number(value)
    return Number.isNaN(n) ? String(value) : `$${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }
  if (type === 'percent') {
    const n = Number(value)
    return Number.isNaN(n) ? String(value) : `${n.toFixed(2)}%`
  }
  if (type === 'number') {
    const n = Number(value)
    return Number.isNaN(n) ? String(value) : n.toLocaleString()
  }
  return String(value)
}

function cellColor(value: unknown, type?: DataTableSpec['columns'][0]['type']): string {
  if (type === 'percent' || type === 'number') {
    const n = Number(value)
    if (!Number.isNaN(n) && n > 0) return 'text-semantic-success'
    if (!Number.isNaN(n) && n < 0) return 'text-semantic-error'
  }
  return 'text-text-body'
}

export function DataTable({ spec }: { spec: DataTableSpec }) {
  return (
    <div className="rounded-xl bg-surface-elevated border border-surface-border overflow-hidden">
      {spec.title && (
        <div className="px-5 py-3 border-b border-surface-border">
          <p className="text-[13px] font-semibold text-text-heading">{spec.title}</p>
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full text-[13px]">
          <thead>
            <tr className="border-b border-surface-border">
              {spec.columns.map((col) => (
                <th
                  key={col.key}
                  className="px-4 py-2.5 text-left text-[11px] font-medium uppercase tracking-wide text-text-secondary"
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {spec.rows.map((row, i) => (
              <tr
                key={i}
                className={`border-b border-surface-border last:border-0 hover:bg-surface-overlay/40 transition-colors ${i % 2 === 1 ? 'bg-surface-overlay/20' : ''}`}
              >
                {spec.columns.map((col) => (
                  <td
                    key={col.key}
                    className={`px-4 py-2.5 ${cellColor(row[col.key], col.type)}`}
                  >
                    {formatCell(row[col.key], col.type)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
