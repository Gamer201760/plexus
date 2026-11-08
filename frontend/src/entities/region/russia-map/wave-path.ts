interface Point {
  readonly x: number
  readonly y: number
}

const NUMBER_PAIR = /(-?\d*\.?\d+)[ ,](-?\d*\.?\d+)/g
const SUBPATH = /M[^M]*/g

function pointsOf(subpath: string): Point[] {
  return Array.from(subpath.matchAll(NUMBER_PAIR), (match) => ({
    x: Number(match[1]),
    y: Number(match[2]),
  }))
}

function extent(points: readonly Point[]): number {
  let minX = Number.POSITIVE_INFINITY
  let minY = Number.POSITIVE_INFINITY
  let maxX = Number.NEGATIVE_INFINITY
  let maxY = Number.NEGATIVE_INFINITY
  for (const point of points) {
    minX = Math.min(minX, point.x)
    minY = Math.min(minY, point.y)
    maxX = Math.max(maxX, point.x)
    maxY = Math.max(maxY, point.y)
  }
  return Math.max(maxX - minX, maxY - minY)
}

function thinned(points: readonly Point[], step: number): Point[] {
  const kept: Point[] = []
  for (const point of points) {
    const last = kept[kept.length - 1]
    if (last === undefined || Math.hypot(point.x - last.x, point.y - last.y) >= step) {
      kept.push(point)
    }
  }
  return kept
}

function format(value: number): string {
  return String(Math.round(value * 10) / 10)
}

export function wavePath(path: string, step: number, minSize: number): string {
  const rings = Array.from(path.matchAll(SUBPATH), (match) => pointsOf(match[0]))
  const largest = Math.max(0, ...rings.map(extent))
  const threshold = Math.min(largest, minSize)
  return rings
    .filter((points) => points.length > 2 && extent(points) >= threshold)
    .map((points) => thinned(points, step))
    .filter((points) => points.length > 2)
    .map(
      (points) => `M${points.map((point) => `${format(point.x)},${format(point.y)}`).join("L")}Z`,
    )
    .join("")
}
