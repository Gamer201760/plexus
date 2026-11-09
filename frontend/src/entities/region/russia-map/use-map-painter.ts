import { type RefObject, useLayoutEffect, useRef } from "react"
import type { Box } from "./map-motion"
import { MapPainter, type PaintRegion } from "./map-painter"
import type { MapCamera } from "./use-map-camera"

export function useMapPainter(
  surface: RefObject<HTMLDivElement | null>,
  frame: Box,
  regions: readonly PaintRegion[],
  stepOf: (id: string) => number,
  selected: string | null,
  camera: MapCamera,
) {
  const painter = useRef<MapPainter | null>(null)
  useLayoutEffect(() => {
    const element = surface.current
    if (!element) return
    painter.current = new MapPainter(element, frame, regions)
    camera.draw.current = (view, phase) =>
      painter.current?.draw(view, camera.metrics.current, phase)
    camera.cover.current = (views) => painter.current?.cover(views)
    return () => {
      painter.current = null
      camera.draw.current = () => undefined
      camera.cover.current = () => undefined
    }
  }, [surface, camera, frame, regions])

  useLayoutEffect(() => {
    const element = surface.current
    if (!element) return
    const style = getComputedStyle(element)
    const token = (name: string) => style.getPropertyValue(name).trim()
    painter.current?.configure(
      {
        fills: [
          token("--map-none"),
          ...Array.from({ length: 7 }, (_, i) => token(`--data-seq-${i + 1}`)),
        ],
        water: token("--map-water"),
        border: token("--map-border"),
        selected: token("--iso-1"),
        hover: token("--map-hover"),
        line: Number.parseFloat(token("--hairline")),
        selectedLine: Number.parseFloat(token("--iso-line-strong")),
        waves: [token("--iso-1"), token("--iso-2")],
        waveReach: Number.parseFloat(token("--map-wave-reach")),
      },
      new Map(regions.map((region) => [region.id, stepOf(region.id)])),
      selected,
    )
    camera.draw.current(camera.current.current, camera.busy.current ? "moving" : "settled")
  }, [surface, camera, regions, selected, stepOf])
  return painter
}
