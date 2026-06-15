/** Non‑negative finite token count; anything else → 0 (avoids NaN from bad SSE/API). */
export function coerceTokenCount(value: unknown): number {
  if (typeof value === 'number' && Number.isFinite(value) && value >= 0) {
    return Math.floor(value)
  }
  if (typeof value === 'string' && value.trim() !== '') {
    const n = Number(value.trim())
    if (Number.isFinite(n) && n >= 0) return Math.floor(n)
  }
  return 0
}
