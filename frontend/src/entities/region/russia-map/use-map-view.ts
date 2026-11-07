import { type PointerEvent, useCallback, useRef, useState, type WheelEvent } from "react"

export interface MapView {
  readonly scale: number
  readonly x: number
  readonly y: number
}

export interface Box {
  readonly x: number
  readonly y: number
  readonly width: number
  readonly height: number
}

const MIN_SCALE = 1
const MAX_SCALE = 12
const WHEEL_STEP = 1.18
const FIT_PADDING = 0.78

const clampScale = (scale: number) => Math.min(MAX_SCALE, Math.max(MIN_SCALE, scale))

export function useMapView(frame: Box) {
  const [view, setView] = useState<MapView>({ scale: 1, x: 0, y: 0 })
  const [dragging, setDragging] = useState(false)
  const drag = useRef<{ id: number; px: number; py: number; moved: boolean } | null>(null)
  const svgRef = useRef<SVGSVGElement | null>(null)
  const justDragged = useRef(false)

  const toLocal = useCallback(
    (clientX: number, clientY: number) => {
      const rect = svgRef.current?.getBoundingClientRect()
      if (!rect || rect.width === 0) return { x: frame.x, y: frame.y, k: 1 }
      const k = Math.max(frame.width / rect.width, frame.height / rect.height)
      const offsetX = (rect.width * k - frame.width) / 2
      const offsetY = (rect.height * k - frame.height) / 2
      return {
        x: frame.x + (clientX - rect.left) * k - offsetX,
        y: frame.y + (clientY - rect.top) * k - offsetY,
        k,
      }
    },
    [frame],
  )

  const zoomAt = useCallback((factor: number, cx: number, cy: number) => {
    setView((current) => {
      const scale = clampScale(current.scale * factor)
      const ratio = scale / current.scale
      return { scale, x: cx - (cx - current.x) * ratio, y: cy - (cy - current.y) * ratio }
    })
  }, [])

  const zoomBy = useCallback(
    (factor: number) => zoomAt(factor, frame.x + frame.width / 2, frame.y + frame.height / 2),
    [frame, zoomAt],
  )

  const reset = useCallback(() => setView({ scale: 1, x: 0, y: 0 }), [])

  const fitBox = useCallback(
    (box: Box) => {
      const scale = clampScale(
        Math.min(frame.width / box.width, frame.height / box.height) * FIT_PADDING,
      )
      const cx = box.x + box.width / 2
      const cy = box.y + box.height / 2
      const fx = frame.x + frame.width / 2
      const fy = frame.y + frame.height / 2
      setView({ scale, x: fx - cx * scale, y: fy - cy * scale })
    },
    [frame],
  )

  const onWheel = useCallback(
    (event: WheelEvent<SVGSVGElement>) => {
      const point = toLocal(event.clientX, event.clientY)
      zoomAt(event.deltaY < 0 ? WHEEL_STEP : 1 / WHEEL_STEP, point.x, point.y)
    },
    [toLocal, zoomAt],
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
      setView((current) => ({ ...current, x: current.x + dx, y: current.y + dy }))
    },
    [toLocal],
  )

  const onPointerUp = useCallback(() => {
    justDragged.current = drag.current?.moved ?? false
    drag.current = null
    setDragging(false)
  }, [])

  const wasDrag = useCallback(() => justDragged.current, [])

  return {
    view,
    dragging,
    svgRef,
    zoomBy,
    reset,
    fitBox,
    wasDrag,
    handlers: { onWheel, onPointerDown, onPointerMove, onPointerUp, onPointerCancel: onPointerUp },
  }
}
