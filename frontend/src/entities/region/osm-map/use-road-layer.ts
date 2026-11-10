import type { Map as LibreMap, MapLayerMouseEvent } from "maplibre-gl"
import { type RefObject, useEffect, useRef } from "react"
import type { RoadLayerProps, RoadSegment } from "@/shared/api/road-graph"
import { drawConnection } from "./connection-layer"
import { REGIONS_SOURCE } from "./osm-style"
import { roadLayers } from "./road-parts"
import { drawRoadParts, selectRoads } from "./road-source"
import { useAnalysisLayer } from "./use-analysis-layer"
import { useCorridorLayer } from "./use-corridor-layer"

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
  const current = useRef({ onRoad, selected })
  current.current = { onRoad, selected }
  const onRendering = roads?.onRendering
  useEffect(() => {
    const map = engine.current
    if (!ready || !map?.getSource(REGIONS_SOURCE)) return
    const controller = new AbortController()
    map.getContainer().dataset.roadRendering = "true"
    onRendering?.(true)
    void drawRoadParts(
      map,
      view?.geometry ?? [],
      controller.signal,
      () => current.current.selected ?? [],
    )
      .then(() => {
        if (!controller.signal.aborted)
          map.getContainer().dataset.roadSegments = String(view?.segmentCount ?? 0)
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) console.error(error)
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          map.getContainer().dataset.roadRendering = "false"
          onRendering?.(false)
        }
      })
    return () => {
      controller.abort()
    }
  }, [engine, view, ready, onRendering])

  useEffect(() => {
    const map = engine.current
    if (ready && map) selectRoads(map, selected ?? [])
  }, [engine, selected, ready])

  useEffect(() => {
    const map = engine.current
    if (!ready || !map) return
    const click = (event: MapLayerMouseEvent) => {
      const layers = roadLayers(map)
      if (!layers.length) return
      const feature = map.queryRenderedFeatures(event.point, { layers })[0]
      if (feature?.geometry.type !== "LineString") return
      const properties = feature.properties as Omit<RoadSegment, "coordinates">
      current.current.onRoad?.({ ...properties, coordinates: feature.geometry.coordinates })
    }
    map.on("click", click)
    return () => {
      map.off("click", click)
    }
  }, [engine, ready])

  useEffect(() => {
    const map = engine.current
    if (ready && map?.getSource(REGIONS_SOURCE)) drawConnection(map, addition)
  }, [engine, addition, ready])
}
