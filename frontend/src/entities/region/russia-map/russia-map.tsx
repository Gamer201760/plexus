import clsx from "clsx"
import { type ReactNode, useEffect, useMemo, useState } from "react"
import type { Box } from "./map-motion"
import styles from "./russia-map.module.css"
import { SelectionWaves } from "./selection-waves"
import { useMapView } from "./use-map-view"

export interface MapRegion {
  readonly id: string
  readonly name: string
  readonly path: string
}

export type MapStep = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7

export interface MapControls {
  readonly zoomIn: () => void
  readonly zoomOut: () => void
  readonly reset: () => void
}

export interface RussiaMapProps {
  readonly viewBox: string
  readonly regions: readonly MapRegion[]
  readonly stepOf: (id: string) => MapStep
  readonly selectedId: string | null
  readonly focusBox: Box | null
  readonly label: string
  readonly onSelect: (id: string) => void
  readonly onHover: (id: string | null, x: number, y: number) => void
  readonly controls: (controls: MapControls) => ReactNode
}

function parseBox(viewBox: string): Box {
  const [x = 0, y = 0, width = 1, height = 1] = viewBox.split(/\s+/).map(Number)
  return { x, y, width, height }
}

export function RussiaMap({
  viewBox,
  regions,
  stepOf,
  selectedId,
  focusBox,
  label,
  onSelect,
  onHover,
  controls,
}: RussiaMapProps) {
  const frame = useMemo(() => parseBox(viewBox), [viewBox])
  const map = useMapView(frame)
  const { fitBox, reset } = map
  const selected = regions.find((region) => region.id === selectedId) ?? null
  const [hoveredId, setHoveredId] = useState<string | null>(null)
  const hovered = regions.find((region) => region.id === hoveredId) ?? null

  useEffect(() => {
    if (focusBox) fitBox(focusBox)
    else reset()
  }, [focusBox, fitBox, reset])

  const transform = `translate(${map.view.x}px, ${map.view.y}px) scale(${map.view.scale})`

  return (
    <div className={styles.frame}>
      <div ref={map.motionRef} className={styles.motion}>
        <svg
          ref={map.svgRef}
          className={clsx(styles.map, map.dragging && styles.dragging)}
          viewBox={viewBox}
          role="img"
          aria-label={label}
          {...map.handlers}
          onPointerLeave={() => {
            setHoveredId(null)
            onHover(null, 0, 0)
          }}
        >
          <g className={styles.layer} style={{ transform }}>
            {regions.map((region) => (
              // biome-ignore lint/a11y/noStaticElementInteractions: regions are pointer shortcuts, keyboard users pick regions through search and the region list
              <path
                key={region.id}
                className={styles.region}
                data-step={stepOf(region.id)}
                data-selected={region.id === selectedId || undefined}
                d={region.path}
                onPointerMove={(event) => {
                  if (event.pointerType === "mouse") setHoveredId(region.id)
                  onHover(region.id, event.clientX, event.clientY)
                }}
                onClick={() => {
                  if (!map.wasDrag()) onSelect(region.id)
                }}
              />
            ))}
          </g>
        </svg>
        {hovered && !map.dragging ? (
          <svg
            key={hovered.id}
            className={clsx(styles.overlay, styles.hover)}
            viewBox={viewBox}
            aria-hidden="true"
          >
            <g className={styles.layer} style={{ transform }}>
              <path d={hovered.path} />
            </g>
          </svg>
        ) : null}
        {selected ? (
          <>
            <svg className={styles.overlay} viewBox={viewBox} aria-hidden="true">
              <g className={styles.layer} style={{ transform }}>
                <SelectionWaves
                  key={selected.id}
                  path={selected.path}
                  unit={map.unit / map.view.scale}
                />
              </g>
            </svg>
            <svg className={styles.overlay} viewBox={viewBox} aria-hidden="true">
              <g className={styles.layer} style={{ transform }}>
                <path
                  className={clsx(styles.region, styles.selected)}
                  data-step={stepOf(selected.id)}
                  d={selected.path}
                />
              </g>
            </svg>
          </>
        ) : null}
      </div>
      {controls({ zoomIn: () => map.zoomBy(1.6), zoomOut: () => map.zoomBy(1 / 1.6), reset })}
    </div>
  )
}
