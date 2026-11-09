import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { motionMs, useReducedMotion } from "@/shared/motion"
import { constrainView, HOME, type MapMetrics } from "./map-gesture"
import { type Box, type DrawPhase, flightPath, type MapView } from "./map-motion"

export function useMapCamera(frame: Box) {
  const [view, setView] = useState<MapView>(HOME)
  const [active, setActive] = useState(false)
  const frameRef = useRef<HTMLDivElement | null>(null)
  const current = useRef(HOME)
  const draw = useRef<(view: MapView, phase: DrawPhase) => void>(() => undefined)
  const cover = useRef<(views: readonly MapView[]) => void>(() => undefined)
  const raf = useRef<number | null>(null)
  const busy = useRef(false)
  const metrics = useRef<MapMetrics>({ width: 0, height: 0, left: 0, top: 0 })
  const reduced = useReducedMotion()
  const flight = useRef(0)

  const cancelFrame = useCallback(() => {
    if (raf.current !== null) cancelAnimationFrame(raf.current)
    raf.current = null
  }, [])

  const paint = useCallback(() => {
    raf.current = null
    draw.current(current.current, "moving")
  }, [])

  const begin = useCallback(
    (measure = true) => {
      if (busy.current) return
      cancelFrame()
      const rect =
        measure || metrics.current.width === 0 ? frameRef.current?.getBoundingClientRect() : null
      if (rect)
        metrics.current = { width: rect.width, height: rect.height, left: rect.left, top: rect.top }
      busy.current = true
      setActive(true)
    },
    [cancelFrame],
  )

  const move = useCallback(
    (next: MapView) => {
      current.current = constrainView(next, frame)
      if (raf.current === null) raf.current = requestAnimationFrame(paint)
    },
    [frame, paint],
  )

  const commit = useCallback(() => {
    cancelFrame()
    busy.current = false
    draw.current(current.current, "settled")
    setView({ ...current.current })
    setActive(false)
  }, [cancelFrame])

  const flyTo = useCallback(
    (target: MapView, instant = false) => {
      begin(false)
      cancelFrame()
      const from = current.current
      const next = constrainView(target, frame)
      if (
        reduced ||
        instant ||
        (from.x === next.x && from.y === next.y && from.scale === next.scale)
      ) {
        current.current = next
        commit()
        return
      }
      const path = flightPath(from, next, frame).frames
      cover.current(path)
      const duration = flight.current || motionMs("--dur-panel", frameRef.current ?? undefined)
      const start = performance.now()
      busy.current = false
      const tick = (now: number) => {
        const progress = Math.min(1, (now - start) / duration)
        const index = progress * (path.length - 1)
        const left = path[Math.floor(index)] ?? from
        const right = path[Math.min(path.length - 1, Math.ceil(index))] ?? next
        const mix = index - Math.floor(index)
        current.current = {
          scale: left.scale + (right.scale - left.scale) * mix,
          x: left.x + (right.x - left.x) * mix,
          y: left.y + (right.y - left.y) * mix,
        }
        draw.current(current.current, "flying")
        if (progress < 1) raf.current = requestAnimationFrame(tick)
        else {
          current.current = next
          commit()
        }
      }
      raf.current = requestAnimationFrame(tick)
    },
    [begin, cancelFrame, commit, frame, reduced],
  )

  useEffect(() => {
    const element = frameRef.current
    if (!element) return
    flight.current = motionMs("--dur-panel", element)
    const measure = () => {
      const rect = element.getBoundingClientRect()
      const resized = metrics.current.width !== rect.width || metrics.current.height !== rect.height
      metrics.current = { width: rect.width, height: rect.height, left: rect.left, top: rect.top }
      if (resized) commit()
      else draw.current(current.current, raf.current === null ? "settled" : "moving")
    }
    const observer = new ResizeObserver(measure)
    observer.observe(element)
    return () => {
      observer.disconnect()
      cancelFrame()
    }
  }, [cancelFrame, commit])

  const camera = useMemo(
    () => ({ begin, move, commit, flyTo, current, metrics, busy, draw, cover }),
    [begin, move, commit, flyTo],
  )
  return { view, active, frameRef, camera }
}

export type MapCamera = ReturnType<typeof useMapCamera>["camera"]
