import type { FeatureCollection, LineString } from "geojson"
import type { GeoJSONSource, Map as LibreMap } from "maplibre-gl"
import type { RoadJob } from "@/shared/api/road-graph"

const CONNECTION_LAYER = "scenario-connection"

export function drawConnection(map: LibreMap, addition: RoadJob["addition"] | undefined) {
  const data: FeatureCollection<LineString> = {
    type: "FeatureCollection",
    features: addition?.coordinates
      ? [
          {
            type: "Feature",
            properties: {},
            geometry: { type: "LineString", coordinates: addition.coordinates },
          },
        ]
      : [],
  }
  if (!map.getSource(CONNECTION_LAYER)) {
    map.addSource(CONNECTION_LAYER, { type: "geojson", data })
    map.addLayer({
      id: CONNECTION_LAYER,
      type: "line",
      source: CONNECTION_LAYER,
      paint: {
        "line-color": getComputedStyle(map.getContainer()).getPropertyValue("--data-gain-3").trim(),
        "line-width": 4,
        "line-dasharray": [2, 2],
      },
    })
  } else {
    ;(map.getSource(CONNECTION_LAYER) as GeoJSONSource).setData(data)
  }
}
