import {
  type PointerEvent,
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type WheelEvent,
} from "react"
import { motionMs, readEasing } from "@/shared/motion"
import {
  type Box,
  composeTransforms,
  flightPath,
  type MapView,
  type Size,
  unitsPerPixel,
  viewShift,
} from "./map-motion"

export type { Box, MapView } from "./map-motion"

interface Flight {
  readonly view: MapView
  readonly anim: Animation | null
  readonly keyframes?: Keyframe[]
  readonly duration?: number
}

const HOME: MapView = { scale: 1, x: 0, y: 0 }
const MIN_SCALE = 1
const MAX_SCALE = 12
const WHEEL_STEP = 1.18
const FIT_SHARE = 0.5
const MAX_FIT_SCALE = 6

const clampScale = (scale: number) => Math.min(MAX_SCALE, Math.max(MIN_SCALE, scale))

function sizeOf(svg: SVGSVGElement | null): Size {
  return { width: svg?.clientWidth ?? 0, height: svg?.clientHeight ?? 0 }
}

function useUnitsPerPixel(svgRef: { readonly current: SVGSVGElement | null }, frame: Box) {
  const [unit, setUnit] = useState(1)
  useEffect(() => {
    const svg = svgRef.current
    const measure = () => setUnit(unitsPerPixel(frame, sizeOf(svg)))
    measure()
    if (svg === null || typeof ResizeObserver === "undefined") return
    const observer = new ResizeObserver(measure)
    observer.observe(svg)
    return () => observer.disconnect()
  }, [svgRef, frame])
  return unit
}

function flightOptions(element: Element, duration: number): KeyframeAnimationOptions {
  return { duration, easing: readEasing("--ease-linear", element) }
}

export function useMapView(frame: Box) {
  const [view, setView] = useState<MapView>(HOME)
  const [dragging, setDragging] = useState(false)
  const shown = useRef<MapView>(HOME)
  const goal = useRef<MapView>(HOME)
  const flight = useRef<Flight | null>(null)
  const drag = useRef<{ id: number; px: number; py: number; moved: boolean } | null>(null)
  const svgRef = useRef<SVGSVGElement | null>(null)
  const motionRef = useRef<HTMLDivElement | null>(null)
  const justDragged = useRef(false)
  const unit = useUnitsPerPixel(svgRef, frame)

  useLayoutEffect(() => {
    shown.current = view
    const current = flight.current
    const layer = motionRef.current
    if (current === null || current.view !== view) return
    if (current.keyframes === undefined || layer === null) {
      current.anim?.cancel()
      flight.current = null
      return
    }
    const anim = layer.animate(current.keyframes, flightOptions(layer, current.duration ?? 0))
    flight.current = { view, anim }
    anim.onfinish = () => {
      if (flight.current?.anim === anim) flight.current = null
    }
  }, [view])

  const jump = useCallback((next: MapView) => {
    const current = flight.current
    if (current?.anim) {
      current.anim.onfinish = null
      current.anim.pause()
    }
    flight.current = current?.anim ? { view: next, anim: current.anim } : null
    goal.current = next
    setView(next)
  }, [])

  const flyTo = useCallback(
    (next: MapView) => {
      const layer = motionRef.current
      const size = sizeOf(svgRef.current)
      const current = flight.current
      if (
        layer === null ||
        typeof layer.animate !== "function" ||
        size.width === 0 ||
        current?.keyframes !== undefined
      ) {
        jump(next)
        return
      }
      const now = current?.anim ? getComputedStyle(layer).transform : "none"
      current?.anim?.cancel()
      const from = shown.current
      goal.current = next
      const path = flightPath(from, next, frame)
      const duration = motionMs("--dur-map", layer) * (1 + path.reach)
      const base = next.scale < from.scale ? next : from
      const keyframes: Keyframe[] = path.frames.map((view) => ({
        transform: viewShift(base, view, frame, size),
      }))
      keyframes[0] = {
        transform: base === from ? now : composeTransforms(now, viewShift(next, from, frame, size)),
      }
      if (base === next) {
        flight.current = { view: next, anim: null, keyframes, duration }
        setView(next)
        return
      }
      const anim = layer.animate(keyframes, { ...flightOptions(layer, duration), fill: "forwards" })
      flight.current = { view: next, anim }
      anim.onfinish = () => {
        if (flight.current?.anim === anim) setView(next)
      }
    },
    [frame, jump],
  )

  const toLocal = useCallback(
    (clientX: number, clientY: number) => {
      const svg = svgRef.current
      const rect = svg?.parentElement?.parentElement?.getBoundingClientRect()
      const size = sizeOf(svg)
      if (!rect || size.width === 0) return { x: frame.x, y: frame.y, k: 1 }
      const k = unitsPerPixel(frame, size)
      const offsetX = (size.width * k - frame.width) / 2
      const offsetY = (size.height * k - frame.height) / 2
      return {
        x: frame.x + (clientX - rect.left) * k - offsetX,
        y: frame.y + (clientY - rect.top) * k - offsetY,
        k,
      }
    },
    [frame],
  )

  const scaledAt = useCallback((factor: number, cx: number, cy: number): MapView => {
    const current = goal.current
    const scale = clampScale(current.scale * factor)
    const ratio = scale / current.scale
    return { scale, x: cx - (cx - current.x) * ratio, y: cy - (cy - current.y) * ratio }
  }, [])

  const zoomBy = useCallback(
    (factor: number) =>
      flyTo(scaledAt(factor, frame.x + frame.width / 2, frame.y + frame.height / 2)),
    [frame, flyTo, scaledAt],
  )

  const reset = useCallback(() => flyTo(HOME), [flyTo])

  const fitBox = useCallback(
    (box: Box) => {
      const fit = Math.min(frame.width / box.width, frame.height / box.height) * FIT_SHARE
      const scale = clampScale(Math.min(MAX_FIT_SCALE, fit))
      const cx = box.x + box.width / 2
      const cy = box.y + box.height / 2
      const fx = frame.x + frame.width / 2
      const fy = frame.y + frame.height / 2
      flyTo({ scale, x: fx - cx * scale, y: fy - cy * scale })
    },
    [frame, flyTo],
  )

  const onWheel = useCallback(
    (event: WheelEvent<SVGSVGElement>) => {
      const point = toLocal(event.clientX, event.clientY)
      jump(scaledAt(event.deltaY < 0 ? WHEEL_STEP : 1 / WHEEL_STEP, point.x, point.y))
    },
    [toLocal, jump, scaledAt],
  )

  const onPointerDown = useCallback((event: PointerEvent<SVGSVGElement>) => {
    justDragged.current = false
    drag.current = { id: event.pointerId, px: event.clientX, py: event.clientY, moved: false }
  }, [])

  const onPointerMove = useCallback(
    (event: PointerEvent<SVGSVGElement>) => {
      const state = drag.current
      if (!state || state.id !== event.pointerId) return
      const { k } = toLocal(event.clientX, event.clientY)
      const dx = (event.clientX - state.px) * k
      const dy = (event.clientY - state.py) * k
      if (!state.moved && Math.hypot(dx, dy) < 4 * k) return
      if (!state.moved) {
        state.moved = true
        setDragging(true)
        event.currentTarget.setPointerCapture(event.pointerId)
      }
      state.px = event.clientX
      state.py = event.clientY
      const current = goal.current
      jump({ ...current, x: current.x + dx, y: current.y + dy })
    },
    [toLocal, jump],
  )

  const onPointerUp = useCallback(() => {
    justDragged.current = drag.current?.moved ?? false
    drag.current = null
    setDragging(false)
  }, [])

  const wasDrag = useCallback(() => justDragged.current, [])

  return {
    view,
    unit,
    dragging,
    svgRef,
    motionRef,
    zoomBy,
    reset,
    fitBox,
    wasDrag,
    handlers: { onWheel, onPointerDown, onPointerMove, onPointerUp, onPointerCancel: onPointerUp },
  }
}
