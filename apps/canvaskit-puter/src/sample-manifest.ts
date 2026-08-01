import type { UIManifest } from './types/canvas'

// Bundled fallback so the app renders with zero backend — used when window.puter
// is unavailable (opened outside Puter) or no manifest has been written yet.
// Mirrors the shape the Orcha finance-dashboard agent emits.
export const SAMPLE_MANIFEST: UIManifest = {
  version: '1.0',
  title: 'Portfolio Overview — sample data',
  layout: 'dashboard',
  components: [
    { type: 'metric_card', id: 'm1', label: 'Total Value', value: 128450, unit: 'USD', delta: 3.2, trend: 'up', sub_label: 'vs. last week' },
    { type: 'metric_card', id: 'm2', label: 'Day P/L', value: 1840, unit: 'USD', delta: 1.4, trend: 'up', sub_label: 'today' },
    { type: 'metric_card', id: 'm3', label: 'Cash', value: 22300, unit: 'USD', trend: 'flat', sub_label: 'available' },
    { type: 'metric_card', id: 'm4', label: 'Positions', value: 12, trend: 'flat', sub_label: 'open' },
    {
      type: 'line_chart',
      id: 'lc1',
      title: 'Portfolio value (30d)',
      x_key: 'day',
      y_keys: ['value'],
      data: [
        { day: 'Wk1', value: 119000 },
        { day: 'Wk2', value: 121500 },
        { day: 'Wk3', value: 118200 },
        { day: 'Wk4', value: 124900 },
        { day: 'Now', value: 128450 },
      ],
    },
    {
      type: 'data_table',
      id: 'dt1',
      title: 'Top holdings',
      columns: [
        { key: 'symbol', label: 'Symbol', type: 'text' },
        { key: 'shares', label: 'Shares', type: 'number' },
        { key: 'value', label: 'Value', type: 'currency' },
        { key: 'change', label: 'Day %', type: 'percent' },
      ],
      rows: [
        { symbol: 'NVDA', shares: 40, value: 48200, change: 2.9 },
        { symbol: 'AAPL', shares: 120, value: 27600, change: -0.8 },
        { symbol: 'MSFT', shares: 30, value: 14100, change: 1.1 },
        { symbol: 'AMZN', shares: 55, value: 10900, change: 0.4 },
      ],
    },
    {
      type: 'alert_feed',
      id: 'af1',
      title: 'Signals',
      alerts: [
        { id: 'a1', severity: 'success', title: 'NVDA up 2.9% on earnings coverage', timestamp: '09:41' },
        { id: 'a2', severity: 'warning', title: 'AAPL below 20-day moving average', body: 'Consider reviewing the position.', timestamp: '09:58' },
        { id: 'a3', severity: 'info', title: 'Cash allocation at 17%', timestamp: '10:03' },
      ],
    },
  ],
}
