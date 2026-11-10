import type { RoadBounds } from "@/shared/api/road-graph"

function detail(zoom: number) {
  return zoom < 5 ? 4 : zoom < 7 ? 6 : zoom < 9 ? 8 : 10
}

export function coversRoadViewport(coverage: RoadBounds, visible: RoadBounds): boolean {
  return (
    coverage[4] === detail(visible[4]) &&
    coverage[0] <= visible[0] &&
    coverage[1] <= visible[1] &&
    coverage[2] >= visible[2] &&
    coverage[3] >= visible[3]
  )
}

export function roadViewport(bounds: RoadBounds): RoadBounds {
  const [west, south, east, north, zoom] = bounds
  const paddingX = (east - west) * 0.1
  const paddingY = (north - south) * 0.1
  const cell = 2 ** Math.floor(Math.log2(Math.max(east - west, north - south) / 16))
  return [
    Math.max(-180, Math.floor((west - paddingX) / cell) * cell),
    Math.max(-85, Math.floor((south - paddingY) / cell) * cell),
    Math.min(180, Math.ceil((east + paddingX) / cell) * cell),
    Math.min(85, Math.ceil((north + paddingY) / cell) * cell),
    detail(zoom),
  ]
}
