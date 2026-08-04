export interface WingCell {
  x: number
  y: number
  fill: string
}

const P = 1.35
const W = 'var(--owl-wing)'
const S = 'var(--owl-wing-shadow)'

const LEFT_WING = { cx: 25, cy: 65, rx: 11.2, ry: 14.5, y0: 52, y1: 79 }

function snap(value: number): number {
  return Math.round(value / P) * P
}

function buildLeftWing(): WingCell[] {
  const { cx, cy, rx, ry, y0, y1 } = LEFT_WING
  const cells: WingCell[] = []
  const seen = new Set<string>()

  for (let y = y0; y <= y1; y += P) {
    for (let x = cx - rx; x <= cx + 0.01; x += P) {
      const sx = snap(x)
      const sy = snap(y)
      const key = `${sx},${sy}`
      if (seen.has(key)) continue

      const dx = sx - cx
      const dy = sy - cy
      if (dx > 0.01) continue
      if ((dx * dx) / (rx * rx) + (dy * dy) / (ry * ry) > 1) continue

      seen.add(key)
      const norm = Math.sqrt((dx * dx) / (rx * rx) + (dy * dy) / (ry * ry))
      cells.push({ x: sx, y: sy, fill: norm > 0.62 ? S : W })
    }
  }

  return cells
}

function mirrorWing(cells: WingCell[]): WingCell[] {
  return cells.map((c) => ({
    x: snap(100 - c.x),
    y: c.y,
    fill: c.fill,
  }))
}

export function buildWings(): { left: WingCell[]; right: WingCell[] } {
  const left = buildLeftWing()
  return { left, right: mirrorWing(left) }
}

export const WING_RECT_SIZE = P

export const WING_LEFT_ORIGIN = { x: LEFT_WING.cx, y: LEFT_WING.cy }
export const WING_RIGHT_ORIGIN = { x: 100 - LEFT_WING.cx, y: LEFT_WING.cy }
