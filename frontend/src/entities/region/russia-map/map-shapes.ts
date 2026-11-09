import type { Box } from "./map-motion"

interface Point {
  readonly x: number
  readonly y: number
}

function points(path: string): Point[] {
  return Array.from(path.matchAll(/(-?\d*\.?\d+)[ ,](-?\d*\.?\d+)/g), (pair) => ({
    x: Number(pair[1]),
    y: Number(pair[2]),
  }))
}

function bounds(vertices: readonly Point[]): Box {
  const xs = vertices.map((point) => point.x)
  const ys = vertices.map((point) => point.y)
  const x = Math.min(...xs),
    y = Math.min(...ys)
  return { x, y, width: Math.max(...xs) - x, height: Math.max(...ys) - y }
}

function area(vertices: readonly Point[]): number {
  let sum = 0
  for (let i = 0; i < vertices.length; i += 1) {
    const a = vertices[i],
      b = vertices[(i + 1) % vertices.length]
    if (a && b) sum += a.x * b.y - b.x * a.y
  }
  return Math.abs(sum) / 2
}

export function mainlandBox(path: string): Box | null {
  let largest: readonly Point[] = []
  let largestArea = 0
  for (const ring of path.matchAll(/M[^M]*/g)) {
    const vertices = points(ring[0])
    const size = area(vertices)
    if (size > largestArea) {
      largest = vertices
      largestArea = size
    }
  }
  return largest.length > 2 ? bounds(largest) : null
}

export function pathBox(path: string): Box {
  return bounds(points(path))
}

export function contains(box: Box, x: number, y: number): boolean {
  return x >= box.x && y >= box.y && x <= box.x + box.width && y <= box.y + box.height
}

export function intersects(a: Box, b: Box): boolean {
  return (
    a.x <= b.x + b.width && a.x + a.width >= b.x && a.y <= b.y + b.height && a.y + a.height >= b.y
  )
}

export function encloses(outer: Box, inner: Box): boolean {
  return (
    inner.x >= outer.x &&
    inner.y >= outer.y &&
    inner.x + inner.width <= outer.x + outer.width &&
    inner.y + inner.height <= outer.y + outer.height
  )
}

export function expand(box: Box, share: number): Box {
  return {
    x: box.x - box.width * share,
    y: box.y - box.height * share,
    width: box.width * (1 + share * 2),
    height: box.height * (1 + share * 2),
  }
}

export function union(a: Box | null, b: Box): Box {
  if (a === null) return b
  const x = Math.min(a.x, b.x)
  const y = Math.min(a.y, b.y)
  return {
    x,
    y,
    width: Math.max(a.x + a.width, b.x + b.width) - x,
    height: Math.max(a.y + a.height, b.y + b.height) - y,
  }
}
