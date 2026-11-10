import type { GeoJSONSource, Map as LibreMap } from "maplibre-gl"
import type { RoadSegment } from "@/shared/api/road-graph"
import { betweenRoadParts, roadLayers, roadPart } from "./road-parts"

export function selectRoads(
  map: LibreMap,
  selected: readonly RoadSegment[],
  layers = roadLayers(map),
) {
  for (const id of layers) {
    map.setPaintProperty(id, "line-width", [
      "case",
      ["in", ["get", "way_id"], ["literal", selected.map((road) => road.way_id)]],
      5,
      1.5,
    ])
  }
}

function removeParts(map: LibreMap, from: number) {
  const count = Number(map.getContainer().dataset.roadParts ?? 0)
  for (let index = from; index < count; index++) {
    const id = roadPart(index)
    if (map.getLayer(id)) map.removeLayer(id)
    if (map.getSource(id)) map.removeSource(id)
  }
  map.getContainer().dataset.roadParts = String(from)
}

export async function drawRoadParts(
  map: LibreMap,
  parts: readonly Blob[],
  signal: AbortSignal,
  selected: () => readonly RoadSegment[],
) {
  if (!parts.length) {
    removeParts(map, 0)
    return
  }
  const color = getComputedStyle(map.getContainer()).getPropertyValue("--series-2").trim()
  for (const [index, part] of parts.entries()) {
    await betweenRoadParts(map, signal)
    if (signal.aborted) return
    const id = roadPart(index)
    if (!map.getSource(id)) {
      map.addSource(id, { type: "geojson", data: { type: "FeatureCollection", features: [] } })
      map.addLayer({
        id,
        type: "line",
        source: id,
        paint: { "line-color": color, "line-width": 1.5 },
      })
    }
    map.getContainer().dataset.roadParts = String(
      Math.max(index + 1, Number(map.getContainer().dataset.roadParts ?? 0)),
    )
    selectRoads(map, selected(), [id])
    const url = URL.createObjectURL(part)
    try {
      await (map.getSource(id) as GeoJSONSource).setData(url)
    } finally {
      URL.revokeObjectURL(url)
    }
    if (signal.aborted) return
  }
  removeParts(map, parts.length)
}
