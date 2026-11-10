import type { Map as LibreMap } from "maplibre-gl"

export const ROAD_LAYER = "road-graph-lines"

export function roadPart(index: number) {
  return index === 0 ? ROAD_LAYER : `${ROAD_LAYER}-${index}`
}

export function roadLayers(map: LibreMap): string[] {
  const count = Number(map.getContainer().dataset.roadParts ?? 0)
  return Array.from({ length: count }, (_, index) => roadPart(index)).filter((id) =>
    map.getLayer(id),
  )
}

export function betweenRoadParts(map: LibreMap, signal: AbortSignal): Promise<void> {
  return new Promise((resolve) => {
    let frame = 0
    const finish = () => {
      cancelAnimationFrame(frame)
      map.off("moveend", next)
      signal.removeEventListener("abort", finish)
      resolve()
    }
    const next = () => {
      frame = requestAnimationFrame(finish)
    }
    signal.addEventListener("abort", finish, { once: true })
    if (signal.aborted) finish()
    else if (map.isMoving()) map.once("moveend", next)
    else next()
  })
}
