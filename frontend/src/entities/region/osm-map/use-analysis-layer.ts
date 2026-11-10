import type { FeatureCollection, Geometry } from "geojson"
import type { GeoJSONSource, Map as LibreMap } from "maplibre-gl"
import { type RefObject, useEffect, useRef } from "react"
import type { AnalysisDetail, AnalysisOverlay } from "@/shared/api/road-analysis"
import { motionMs, useReducedMotion } from "@/shared/motion"
import { REGIONS_SOURCE } from "./osm-style"

const SOURCE = "road-analysis-result"

export function useAnalysisLayer(
  engine: RefObject<LibreMap | null>,
  overlay: AnalysisOverlay | null | undefined,
  ready: boolean,
) {
  const reduced = useReducedMotion()
  const lastFocus = useRef(0)
  useEffect(() => {
    const map = engine.current
    if (!ready || !map?.getSource(REGIONS_SOURCE)) return
    const detail = overlay?.detail
    const data = analysisFeatures(detail)
    if (!map.getSource(SOURCE)) {
      const style = getComputedStyle(map.getContainer())
      map.addSource(SOURCE, { type: "geojson", data })
      map.addLayer({
        id: `${SOURCE}-line`,
        source: SOURCE,
        type: "line",
        filter: ["==", ["get", "kind"], "road"],
        paint: {
          "line-color": style.getPropertyValue("--action-primary").trim(),
          "line-width": 5,
        },
      })
      map.addLayer({
        id: `${SOURCE}-points`,
        source: SOURCE,
        type: "circle",
        filter: ["==", ["get", "kind"], "settlement"],
        paint: {
          "circle-radius": ["case", ["get", "isolated"], 7, 4],
          "circle-color": [
            "case",
            ["get", "isolated"],
            style.getPropertyValue("--status-danger").trim(),
            style.getPropertyValue("--action-primary").trim(),
          ],
          "circle-stroke-width": 1,
          "circle-stroke-color": style.getPropertyValue("--surface-base").trim(),
        },
      })
    } else (map.getSource(SOURCE) as GeoJSONSource).setData(data)
    map.getContainer().dataset.analysisWay = String(detail?.result.candidate.way_id ?? "")
    if (
      !overlay ||
      overlay.focus === 0 ||
      overlay.focus === lastFocus.current ||
      !detail?.lines.length
    )
      return
    lastFocus.current = overlay.focus
    const [xs, ys] = extent(detail.lines)
    map.stop()
    map.fitBounds(
      [
        [Math.min(...xs), Math.min(...ys)],
        [Math.max(...xs), Math.max(...ys)],
      ],
      {
        padding: 96,
        maxZoom: 12,
        duration: reduced || overlay.instant ? 0 : motionMs("--dur-panel"),
      },
    )
  }, [engine, overlay, ready, reduced])
}

function extent(lines: number[][][]) {
  const coordinates = lines.flat()
  return [
    coordinates.map((p) => {
      const x = p[0] ?? 0
      return x < 0 ? x + 360 : x
    }),
    coordinates.map((p) => p[1] ?? 0),
  ] as const
}

function analysisFeatures(detail: AnalysisDetail | undefined): FeatureCollection<Geometry> {
  const data: FeatureCollection<Geometry> = { type: "FeatureCollection", features: [] }
  if (detail) {
    data.features.push({
      type: "Feature",
      properties: { kind: "road" },
      geometry: { type: "MultiLineString", coordinates: detail.lines },
    })
    for (const point of detail.settlements)
      data.features.push({
        type: "Feature",
        properties: {
          kind: "settlement",
          isolated: point.impact.newly_isolated,
          delta: point.impact.delta,
        },
        geometry: { type: "Point", coordinates: [point.longitude, point.latitude] },
      })
  }
  return data
}
