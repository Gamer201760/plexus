import clsx from "clsx"
import { memo, type PointerEvent, type ReactNode, useEffect, useMemo, useRef } from "react"
import { localPoint } from "./map-gesture"
import type { Box } from "./map-motion"
import { mainlandBox } from "./map-shapes"
import styles from "./russia-map.module.css"
import { useMapPainter } from "./use-map-painter"
import { useMapView } from "./use-map-view"

export interface MapRegion {
  readonly id: string
  readonly name: string
  readonly path: string
  readonly path_low?: string | null
}

export type MapStep = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7

export interface MapControls {
  readonly zoomIn: (instant?: boolean) => void
  readonly zoomOut: (instant?: boolean) => void
  readonly reset: (instant?: boolean) => void
}

export interface RussiaMapProps {
  readonly viewBox: string
  readonly regions: readonly MapRegion[]
  readonly stepOf: (id: string) => MapStep
  readonly selectedId: string | null
  readonly label: string
  readonly onSelect: (id: string) => void
  readonly onHover: (id: string | null, x: number, y: number) => void
  readonly controls: (controls: MapControls) => ReactNode
}

function parseBox(viewBox: string): Box {
  const [x = 0, y = 0, width = 1, height = 1] = viewBox.split(/\s+/).map(Number)
  return { x, y, width, height }
}

export const RussiaMap = memo(function RussiaMap({
  viewBox,
  regions,
  stepOf,
  selectedId,
  label,
  onSelect,
  onHover,
  controls,
}: RussiaMapProps) {
  const frame = useMemo(() => parseBox(viewBox), [viewBox])
  const map = useMapView(frame)
  const { fitBox, reset, active, camera } = map
  const surface = useRef<HTMLDivElement | null>(null)
  const hoverFrame = useRef<number | null>(null)
  const cursor = useRef({ x: 0, y: 0 })
  const painter = useMapPainter(surface, frame, regions, stepOf, selectedId, camera)
  const selected = regions.find((region) => region.id === selectedId)
  const focus = useMemo(() => (selected ? mainlandBox(selected.path) : null), [selected])
  const zoom = useMemo(() => controls(map.controls), [controls, map.controls])

  useEffect(() => {
    if (selectedId && focus) fitBox(focus)
    else if (!selectedId) reset()
  }, [selectedId, focus, fitBox, reset])

  useEffect(() => {
    if (active) onHover(null, 0, 0)
  }, [active, onHover])

  useEffect(
    () => () => {
      if (hoverFrame.current !== null) cancelAnimationFrame(hoverFrame.current)
    },
    [],
  )

  const clearHover = () => {
    if (hoverFrame.current !== null) cancelAnimationFrame(hoverFrame.current)
    hoverFrame.current = null
    painter.current?.hover(null)
    onHover(null, 0, 0)
  }

  const onPointerMove = (event: PointerEvent<HTMLDivElement>) => {
    map.handlers.onPointerMove(event)
    if (camera.busy.current || active || event.pointerType !== "mouse") return
    cursor.current = { x: event.clientX, y: event.clientY }
    if (hoverFrame.current !== null) return
    hoverFrame.current = requestAnimationFrame(() => {
      hoverFrame.current = null
      const point = localPoint(cursor.current, frame, camera.metrics.current)
      const id = painter.current?.pick(point.x, point.y) ?? null
      painter.current?.hover(id)
      onHover(id, cursor.current.x, cursor.current.y)
    })
  }

  return (
    <div ref={map.frameRef} className={styles.frame}>
      {/* biome-ignore lint/a11y/useKeyWithClickEvents: keyboard users select regions through search and the region list */}
      <div
        ref={surface}
        className={clsx(styles.map, active && styles.dragging)}
        role="img"
        aria-label={label}
        data-map-surface
        data-view={JSON.stringify(map.view)}
        {...map.handlers}
        onPointerMove={onPointerMove}
        onPointerEnter={() => {
          const rect = map.frameRef.current?.getBoundingClientRect()
          if (rect)
            camera.metrics.current = {
              left: rect.left,
              top: rect.top,
              width: rect.width,
              height: rect.height,
            }
        }}
        onClick={(event) => {
          if (map.wasDrag()) return
          const point = localPoint(
            { x: event.clientX, y: event.clientY },
            frame,
            camera.metrics.current,
          )
          const id = painter.current?.pick(point.x, point.y)
          if (id) onSelect(id)
        }}
        onPointerLeave={clearHover}
      >
        <div className={styles.stage} data-map-stage>
          <svg className={styles.layer} viewBox={viewBox} aria-hidden="true" />
          <svg className={clsx(styles.layer, styles.hover)} viewBox={viewBox} aria-hidden="true" />
        </div>
      </div>
      {zoom}
    </div>
  )
})
