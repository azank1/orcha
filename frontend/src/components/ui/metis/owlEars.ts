const P = 1.35

const EAR_ANCHOR = { x: 37.2, y: 20.4 }
const EAR_SCALE = 1.88

const LEFT_EAR_BASE: Array<{ x: number; y: number }> = [
  { x: 34.8, y: 14.4 },
  { x: 33.6, y: 15.6 },
  { x: 34.8, y: 15.6 },
  { x: 32.4, y: 16.8 },
  { x: 33.6, y: 16.8 },
  { x: 34.8, y: 16.8 },
  { x: 32.4, y: 18.0 },
  { x: 33.6, y: 18.0 },
  { x: 34.8, y: 18.0 },
  { x: 35.6, y: 18.0 },
  { x: 33.6, y: 19.2 },
  { x: 34.8, y: 19.2 },
  { x: 35.6, y: 19.2 },
  { x: 36.0, y: 19.2 },
  { x: 35.6, y: 20.4 },
]

interface Point {
  x: number
  y: number
}

function snap(value: number): number {
  return Math.round(value / P) * P
}

function round(value: number): number {
  return Math.round(value * 100) / 100
}

function scalePoint(point: { x: number; y: number }): Point {
  return {
    x: snap(EAR_ANCHOR.x + (point.x - EAR_ANCHOR.x) * EAR_SCALE),
    y: snap(EAR_ANCHOR.y + (point.y - EAR_ANCHOR.y) * EAR_SCALE),
  }
}

function uniqueCells(base: Array<{ x: number; y: number }>): Point[] {
  const seen = new Set<string>()
  const cells: Point[] = []
  for (const point of base.map(scalePoint)) {
    const k = `${point.x},${point.y}`
    if (seen.has(k)) continue
    seen.add(k)
    cells.push(point)
  }
  return cells
}

function cellsToSolidPath(cells: Point[]): string {
  return cells
    .map(({ x, y }) => `M${round(x)},${round(y)}h${P}v${P}h${-P}Z`)
    .join('')
}

function mirrorCells(cells: Point[]): Point[] {
  return cells.map((c) => ({ x: snap(100 - c.x - P), y: c.y }))
}

const LEFT_CELLS = uniqueCells(LEFT_EAR_BASE)
export const LEFT_EAR_PATH = cellsToSolidPath(LEFT_CELLS)
export const RIGHT_EAR_PATH = cellsToSolidPath(mirrorCells(LEFT_CELLS))
