import type { FeatureCollection, LineString } from "geojson"
import type { GeoJSONSource, Map as LibreMap } from "maplibre-gl"
import { type RefObject, useEffect } from "react"

const TRANSIT_SOURCE = "region-transit"

export function useTransitLayer(
  engine: RefObject<LibreMap | null>,
  data: FeatureCollection<LineString>,
  ready: boolean,
) {
  useEffect(() => {
    const map = engine.current
    if (!ready || !map) return
    if (!map.getSource(TRANSIT_SOURCE)) {
      addTransitLayers(map, data)
    } else {
      ;(map.getSource(TRANSIT_SOURCE) as GeoJSONSource).setData(data)
    }
    map.getContainer().dataset.transitConnections = String(data.features.length)
  }, [engine, data, ready])
}

function addTransitLayers(map: LibreMap, data: FeatureCollection<LineString>) {
  const colors = getComputedStyle(map.getContainer())
  map.addSource(TRANSIT_SOURCE, { type: "geojson", data })
  for (const mode of ["rail", "air"]) {
    map.addLayer({
      id: `${TRANSIT_SOURCE}-${mode}`,
      type: "line",
      source: TRANSIT_SOURCE,
      filter: ["==", ["get", "mode"], mode],
      paint: {
        "line-color": colors
          .getPropertyValue(mode === "air" ? "--mode-air" : "--text-primary")
          .trim(),
        "line-width": 2,
        "line-opacity": 0.8,
        "line-dasharray": mode === "air" ? [4, 3] : [1, 2],
      },
    })
  }
}
