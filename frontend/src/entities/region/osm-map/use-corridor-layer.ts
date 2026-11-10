import type { FeatureCollection, MultiLineString } from "geojson"
import type { GeoJSONSource, Map as LibreMap } from "maplibre-gl"
import { type RefObject, useEffect, useRef } from "react"
import type { CorridorOverlay } from "@/shared/api/chat-calculation"
import { motionMs, useReducedMotion } from "@/shared/motion"

const SOURCE = "road-corridor-closure"

export function useCorridorLayer(
  engine: RefObject<LibreMap | null>,
  overlay: CorridorOverlay | null | undefined,
  ready: boolean,
) {
  const reduced = useReducedMotion()
  const focused = useRef(0)
  useEffect(() => {
    const map = engine.current
    if (!ready || !map) return
    if (!overlay) {
      clearCorridor(map)
      focused.current = 0
      return
    }
    const lines = overlay.calculation.corridor.lines
    const data: FeatureCollection<MultiLineString> = {
      type: "FeatureCollection",
      features: [
        {
          type: "Feature",
          properties: {},
          geometry: { type: "MultiLineString", coordinates: lines },
        },
      ],
    }
    if (!map.getSource(SOURCE)) {
      map.addSource(SOURCE, { type: "geojson", data })
      map.addLayer({
        id: SOURCE,
        type: "line",
        source: SOURCE,
        paint: {
          "line-color": getComputedStyle(map.getContainer())
            .getPropertyValue("--status-danger")
            .trim(),
          "line-width": 6,
          "line-dasharray": [2, 1],
        },
      })
    } else (map.getSource(SOURCE) as GeoJSONSource).setData(data)
    map.moveLayer(SOURCE)
    map.getContainer().dataset.corridorId = overlay.calculation.corridor.id
    if (focused.current === overlay.focus || !lines.length) return
    focused.current = overlay.focus
    const points = lines.flat()
    const xs = points.map((point) => point[0] ?? 0)
    const ys = points.map((point) => point[1] ?? 0)
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

function clearCorridor(map: LibreMap) {
  if (map.getLayer(SOURCE)) map.removeLayer(SOURCE)
  if (map.getSource(SOURCE)) map.removeSource(SOURCE)
  delete map.getContainer().dataset.corridorId
}
