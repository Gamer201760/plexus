import clsx from "clsx"
import { type CSSProperties, type ReactNode, useEffect, useMemo } from "react"
import styles from "./russia-map.module.css"
import { type Box, useMapView } from "./use-map-view"

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

  useEffect(() => {
    if (focusBox) fitBox(focusBox)
    else reset()
  }, [focusBox, fitBox, reset])

  const transform = `translate(${map.view.x}px, ${map.view.y}px) scale(${map.view.scale})`

  return (
    <div className={styles.frame}>
      <svg
        ref={map.svgRef}
        className={clsx(styles.map, map.dragging && styles.dragging)}
        viewBox={viewBox}
        role="img"
        aria-label={label}
        {...map.handlers}
        onPointerLeave={() => onHover(null, 0, 0)}
      >
        <g
          className={clsx(styles.layer, map.dragging && styles.instant)}
          style={{ transform, "--map-scale": map.view.scale } as CSSProperties}
        >
          {regions.map((region) => (
            // biome-ignore lint/a11y/noStaticElementInteractions: regions are pointer shortcuts, keyboard users pick regions through search and the region list
            <path
              key={region.id}
              className={styles.region}
              data-step={stepOf(region.id)}
              data-selected={region.id === selectedId || undefined}
              d={region.path}
              onPointerMove={(event) => onHover(region.id, event.clientX, event.clientY)}
              onClick={() => {
                if (!map.wasDrag()) onSelect(region.id)
              }}
            />
          ))}
          {selected ? (
            <g className={styles.selection} key={selected.id}>
              <path className={styles.ring3} d={selected.path} />
              <path className={styles.knock3} d={selected.path} />
              <path className={styles.ring2} d={selected.path} />
              <path className={styles.knock2} d={selected.path} />
              <path className={styles.ring1} d={selected.path} />
              <path className={styles.knock1} d={selected.path} />
              <path
                className={styles.region}
                data-step={stepOf(selected.id)}
                data-selected
                d={selected.path}
              />
            </g>
          ) : null}
        </g>
      </svg>
      {controls({ zoomIn: () => map.zoomBy(1.6), zoomOut: () => map.zoomBy(1 / 1.6), reset })}
    </div>
  )
}
