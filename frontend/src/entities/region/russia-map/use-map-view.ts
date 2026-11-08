import { useCallback, useMemo } from "react"
import { HOME, zoomAt } from "./map-gesture"
import type { Box } from "./map-motion"
import { useMapCamera } from "./use-map-camera"
import { useMapGestures } from "./use-map-gestures"

export type { Box, MapView } from "./map-motion"

export function useMapView(frame: Box) {
  const state = useMapCamera(frame)
  const { camera } = state
  const gestures = useMapGestures(frame, state.frameRef, camera)
  const { cancelWheel } = gestures
  const zoomBy = useCallback(
    (factor: number, instant = false) => {
      cancelWheel()
      camera.begin()
      camera.flyTo(
        zoomAt(
          camera.current.current,
          factor,
          {
            x: frame.x + frame.width / 2,
            y: frame.y + frame.height / 2,
          },
          frame,
        ),
        instant,
      )
    },
    [camera, frame, cancelWheel],
  )
  const reset = useCallback(
    (instant = false) => {
      cancelWheel()
      camera.flyTo(HOME, instant)
    },
    [camera, cancelWheel],
  )
  const fitBox = useCallback(
    (box: Box) => {
      cancelWheel()
      const scale = Math.min(
        6,
        Math.max(1, Math.min(frame.width / box.width, frame.height / box.height) * 0.5),
      )
      camera.flyTo({
        scale,
        x: frame.x + frame.width / 2 - (box.x + box.width / 2) * scale,
        y: frame.y + frame.height / 2 - (box.y + box.height / 2) * scale,
      })
    },
    [camera, frame, cancelWheel],
  )
  const controls = useMemo(
    () => ({
      zoomIn: (instant = false) => zoomBy(1.6, instant),
      zoomOut: (instant = false) => zoomBy(1 / 1.6, instant),
      reset,
    }),
    [zoomBy, reset],
  )
  return { ...state, ...gestures, controls, reset, fitBox }
}
