import type { FeatureCollection, LineString } from "geojson"
import type { GeoJSONSource, Map as LibreMap, MapMouseEvent } from "maplibre-gl"
import { type RefObject, useEffect } from "react"
import type { RoadLayerProps } from "@/shared/api/road-graph"
import { drawConnection } from "./connection-layer"
import { REGIONS_SOURCE } from "./osm-style"
import { useAnalysisLayer } from "./use-analysis-layer"
import { useCorridorLayer } from "./use-corridor-layer"

export const ROAD_LAYER = "road-graph-lines"

export function useRoadLayer(
  engine: RefObject<LibreMap | null>,
  roads: RoadLayerProps | undefined,
  ready: boolean,
) {
  useAnalysisLayer(engine, roads?.analysis, ready)
  useCorridorLayer(engine, roads?.corridor, ready)
  const view = roads?.view
  const selected = roads?.selected
  const onRoad = roads?.onRoad
  const addition = roads?.addition
  useEffect(() => {
    const map = engine.current
    if (!ready || !map?.getSource(REGIONS_SOURCE)) return
    const data: FeatureCollection<LineString> = {
      type: "FeatureCollection",
      features: (view?.segments ?? []).map((road, index) => ({
        type: "Feature",
        id: index,
        properties: { way_id: road.way_id },
        geometry: { type: "LineString", coordinates: road.coordinates },
      })),
    }
    if (!map.getSource(ROAD_LAYER)) {
      map.addSource(ROAD_LAYER, { type: "geojson", data })
      map.addLayer({
        id: ROAD_LAYER,
        type: "line",
        source: ROAD_LAYER,
        paint: {
          "line-color": getComputedStyle(map.getContainer()).getPropertyValue("--series-2").trim(),
          "line-width": 1.5,
        },
      })
    } else {
      ;(map.getSource(ROAD_LAYER) as GeoJSONSource).setData(data)
    }
    map.getContainer().dataset.roadSegments = String(data.features.length)
  }, [engine, view, ready])

  useEffect(() => {
    const map = engine.current
    if (!map?.getLayer(ROAD_LAYER)) return
    map.setPaintProperty(ROAD_LAYER, "line-width", [
      "case",
      ["in", ["get", "way_id"], ["literal", (selected ?? []).map((r) => r.way_id)]],
      5,
      1.5,
    ])
    const click = (event: MapMouseEvent) => {
      const found = map.queryRenderedFeatures(event.point, { layers: [ROAD_LAYER] })[0]
      const road = view?.segments.find((r) => r.way_id === found?.properties.way_id)
      if (road) onRoad?.(road)
    }
    map.on("click", click)
    return () => {
      map.off("click", click)
    }
  }, [engine, view, selected, onRoad])

  useEffect(() => {
    const map = engine.current
    if (map?.getSource(REGIONS_SOURCE) && view) drawConnection(map, addition)
  }, [engine, addition, view])
}
