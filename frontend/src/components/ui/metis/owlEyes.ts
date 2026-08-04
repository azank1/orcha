/**
 * Pixel eye grid — forward stare. Pupil is a separate oval;
 * only the outer ring (`g`) changes color with state.
 */
const EYE_ROWS = [
  '.gggg.',
  'gwwwwg',
  'gwwwwg',
  'gwwwwg',
  'gwwwwg',
  'gwwwwg',
  '.gggg.',
] as const

export const EYE_GRID_HEIGHT = EYE_ROWS.length
export const EYE_GRID_WIDTH = Math.max(...EYE_ROWS.map((row) => row.length))

const EYE_FILL_BY_CHAR: Record<string, string> = {
  g: 'var(--owl-eye-glow)',
  w: 'var(--owl-eye-white)',
}

export const PUPIL_RX_RATIO = 0.82
export const PUPIL_RY_RATIO = 1.28

export interface EyeCell {
  x: number
  y: number
  fill: string
}

export interface EyeGeometry {
  cells: EyeCell[]
  center: { x: number; y: number }
}

function buildCells(): EyeCell[] {
  const cells: EyeCell[] = []
  EYE_ROWS.forEach((row, y) => {
    for (let x = 0; x < row.length; x++) {
      const char = row[x]
      if (char === '.') continue
      cells.push({ x, y, fill: EYE_FILL_BY_CHAR[char] })
    }
  })
  return cells
}

function computeCenter(cells: EyeCell[]): { x: number; y: number } {
  let minX = Infinity
  let maxX = -Infinity
  let minY = Infinity
  let maxY = -Infinity

  for (const c of cells) {
    minX = Math.min(minX, c.x)
    maxX = Math.max(maxX, c.x)
    minY = Math.min(minY, c.y)
    maxY = Math.max(maxY, c.y)
  }

  return {
    x: (minX + maxX + 1) / 2,
    y: (minY + maxY + 1) / 2,
  }
}

export function buildEye(): EyeGeometry {
  const cells = buildCells()
  return { cells, center: computeCenter(cells) }
}
