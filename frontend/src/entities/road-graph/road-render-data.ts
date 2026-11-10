import type { FeatureCollection, LineString } from "geojson"
import type { RoadRenderView, RoadView } from "@/shared/api/road-graph"

export function prepareRoadView(view: RoadView): RoadRenderView {
  const choices = new Map<number, RoadView["segments"][number]>()
  const geometry: Blob[] = []
  for (let offset = 0; offset < view.segments.length; offset += 2000) {
    const data: FeatureCollection<LineString> = {
      type: "FeatureCollection",
      features: view.segments.slice(offset, offset + 2000).map((road, index) => {
        if (choices.size < 12 && !choices.has(road.way_id)) choices.set(road.way_id, road)
        const { coordinates, ...properties } = road
        return {
          type: "Feature",
          id: offset + index,
          properties,
          geometry: { type: "LineString", coordinates },
        }
      }),
    }
    geometry.push(new Blob([JSON.stringify(data)], { type: "application/json" }))
  }
  return {
    ...view,
    segments: [...choices.values()],
    segmentCount: view.segments.length,
    geometry,
  }
}
