/**
 * Literal color/font values for recharts (SVG props take real strings, not
 * Tailwind classes) — kept as a single source of truth so chart components
 * never re-inline hex that drifts from the token palette in
 * tailwind.config.ts / index.css. Update in lockstep with those two files.
 */

export const CHART_COLORS = {
  brandPrimary: '#6366F1',
  brandSecondary: '#8B8B96',
  purple: '#A78BFA',
  success: '#22C55E',
  warning: '#F59E0B',
  error: '#EF4444',
} as const

/** Default series/segment color order for multi-series charts. */
export const CHART_COLOR_SEQUENCE: string[] = [
  CHART_COLORS.brandPrimary,
  CHART_COLORS.brandSecondary,
  CHART_COLORS.purple,
  CHART_COLORS.success,
  CHART_COLORS.warning,
  CHART_COLORS.error,
]

/** Matches `--color-text-secondary` — used for axis ticks / legend text. */
export const CHART_TEXT_SECONDARY = '#9CA3AF'

/** Matches `surface.elevated` / `surface.borderLight` — chart tooltip chrome. */
export const CHART_TOOLTIP_STYLE = {
  background: '#18181B',
  border: '1px solid #3F3F46',
  borderRadius: 8,
  fontSize: 12,
  fontFamily: "'JetBrains Mono', ui-monospace, monospace",
} as const

/** Grid lines — a white-tinted overlay reads correctly on any near-black base. */
export const CHART_GRID_STROKE = 'rgba(255,255,255,0.06)'

export const CHART_MONO_FONT_STACK = "'JetBrains Mono', ui-monospace, monospace"
