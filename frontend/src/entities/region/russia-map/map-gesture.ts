import type { Box, MapView, Size } from "./map-motion"
import { unitsPerPixel } from "./map-motion"

export const HOME: MapView = { scale: 1, x: 0, y: 0 }

export interface Point {
  readonly x: number
  readonly y: number
}

export interface MapMetrics extends Size {
  readonly left: number
  readonly top: number
}

export function constrainView(view: MapView, frame: Box): MapView {
  const scale = Math.min(12, Math.max(1, view.scale))
  const right = frame.x * (1 - scale)
  const bottom = frame.y * (1 - scale)
  return {
    scale,
    x: Math.min(right + frame.width * 0.85, Math.max(right - frame.width * (scale - 0.15), view.x)),
    y: Math.min(
      bottom + frame.height * 0.85,
      Math.max(bottom - frame.height * (scale - 0.15), view.y),
    ),
  }
}

export function localPoint(point: Point, frame: Box, size: MapMetrics): Point {
  const unit = unitsPerPixel(frame, size)
  return {
    x: frame.x + (point.x - size.left) * unit - (size.width * unit - frame.width) / 2,
    y: frame.y + (point.y - size.top) * unit - (size.height * unit - frame.height) / 2,
  }
}

export function zoomAt(view: MapView, factor: number, point: Point, frame: Box): MapView {
  const scale = Math.min(12, Math.max(1, view.scale * factor))
  const ratio = scale / view.scale
  return constrainView(
    {
      scale,
      x: point.x - (point.x - view.x) * ratio,
      y: point.y - (point.y - view.y) * ratio,
    },
    frame,
  )
}

export function wheelPixels(delta: number, mode: number, page: number): number {
  return delta * (mode === 1 ? 16 : mode === 2 ? page : 1)
}

export function wheelView(event: WheelEvent, view: MapView, frame: Box, size: MapMetrics): MapView {
  const dx = wheelPixels(event.deltaX, event.deltaMode, size.width)
  const dy = wheelPixels(event.deltaY, event.deltaMode, size.height)
  if (!event.ctrlKey && Math.abs(dx) > Math.abs(dy)) {
    const unit = unitsPerPixel(frame, size)
    return constrainView({ ...view, x: view.x - dx * unit, y: view.y - dy * unit }, frame)
  }
  const point = localPoint({ x: event.clientX, y: event.clientY }, frame, size)
  const sensitivity = event.ctrlKey ? 0.01 : 0.00165
  return zoomAt(view, Math.exp(-Math.max(-600, Math.min(600, dy)) * sensitivity), point, frame)
}
