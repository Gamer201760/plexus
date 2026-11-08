import { type PointerEvent, type RefObject, useCallback, useEffect, useRef } from "react"
import { motionMs } from "@/shared/motion"
import { localPoint, type Point, wheelView, zoomAt } from "./map-gesture"
import type { Box } from "./map-motion"
import type { MapCamera } from "./use-map-camera"

function midpoint(points: readonly Point[]): Point {
  const first = points[0] ?? { x: 0, y: 0 }
  const second = points[1] ?? first
  return { x: (first.x + second.x) / 2, y: (first.y + second.y) / 2 }
}

function distance(points: readonly Point[]): number {
  const a = points[0]
  const b = points[1]
  return a && b ? Math.hypot(a.x - b.x, a.y - b.y) : 0
}

export function useMapGestures(
  frame: Box,
  frameRef: RefObject<HTMLDivElement | null>,
  camera: MapCamera,
) {
  const pointers = useRef(new Map<number, Point>())
  const moved = useRef(false)
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const clearTimer = useCallback(() => {
    if (timer.current !== null) clearTimeout(timer.current)
    timer.current = null
  }, [])

  useEffect(() => {
    const element = frameRef.current
    if (!element) return
    const delay = motionMs("--delay-map-settle", element)
    const wheel = (event: WheelEvent) => {
      if (!(event.target instanceof Element)) return
      if (!event.target.closest("[data-map-surface]")) return
      event.preventDefault()
      if (pointers.current.size > 0) return
      camera.begin()
      camera.move(wheelView(event, camera.current.current, frame, camera.metrics.current))
      clearTimer()
      timer.current = setTimeout(() => {
        timer.current = null
        camera.commit()
      }, delay)
    }
    const gesture = (event: Event) => event.preventDefault()
    element.addEventListener("wheel", wheel, { passive: false })
    element.addEventListener("gesturestart", gesture, { passive: false })
    element.addEventListener("gesturechange", gesture, { passive: false })
    return () => {
      clearTimer()
      element.removeEventListener("wheel", wheel)
      element.removeEventListener("gesturestart", gesture)
      element.removeEventListener("gesturechange", gesture)
    }
  }, [camera, clearTimer, frame, frameRef])

  const onPointerDown = useCallback(
    (event: PointerEvent<HTMLDivElement>) => {
      if (event.button !== 0 || pointers.current.size >= 2) return
      clearTimer()
      if (pointers.current.size === 0) moved.current = false
      pointers.current.set(event.pointerId, { x: event.clientX, y: event.clientY })
      if (pointers.current.size === 2) {
        moved.current = true
        camera.begin()
      }
    },
    [camera, clearTimer],
  )

  const onPointerMove = useCallback(
    (event: PointerEvent<HTMLDivElement>) => {
      const previous = pointers.current.get(event.pointerId)
      if (!previous) return
      const point = { x: event.clientX, y: event.clientY }
      if (!moved.current && Math.hypot(point.x - previous.x, point.y - previous.y) < 4) return
      camera.begin()
      moved.current = true
      event.currentTarget.setPointerCapture(event.pointerId)
      const before = [...pointers.current.values()]
      pointers.current.set(event.pointerId, point)
      const after = [...pointers.current.values()]
      const size = camera.metrics.current
      const start = localPoint(midpoint(before), frame, size)
      const end = localPoint(midpoint(after), frame, size)
      const span = distance(before)
      const view = zoomAt(
        camera.current.current,
        span > 0 ? distance(after) / span : 1,
        start,
        frame,
      )
      camera.move({ ...view, x: view.x + end.x - start.x, y: view.y + end.y - start.y })
    },
    [camera, frame],
  )

  const onPointerUp = useCallback(
    (event: PointerEvent<HTMLDivElement>) => {
      if (!pointers.current.delete(event.pointerId)) return
      if (event.currentTarget.hasPointerCapture(event.pointerId))
        event.currentTarget.releasePointerCapture(event.pointerId)
      if (pointers.current.size === 0 && camera.busy.current) camera.commit()
    },
    [camera],
  )

  const wasDrag = useCallback(() => moved.current, [])
  return {
    wasDrag,
    cancelWheel: clearTimer,
    handlers: {
      onPointerDown,
      onPointerMove,
      onPointerUp,
      onPointerCancel: onPointerUp,
      onLostPointerCapture: onPointerUp,
    },
  }
}
