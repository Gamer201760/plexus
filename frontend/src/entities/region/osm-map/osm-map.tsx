import { memo, type ReactNode, useMemo } from "react"
import { buildBoundaryAtlas, type RegionBoundary } from "./boundary-geojson"
import styles from "./osm-map.module.css"
import { type MapControls, useOsmMap } from "./use-osm-map"

export interface OsmMapProps {
  readonly regions: readonly RegionBoundary[]
  readonly stepOf: (id: string) => number
  readonly selectedId: string | null
  readonly label: string
  readonly attribution: string
  readonly onSelect: (id: string) => void
  readonly onHover: (id: string | null, x: number, y: number) => void
  readonly controls: (controls: MapControls) => ReactNode
}

export const OsmMap = memo(function OsmMap({
  regions,
  stepOf,
  selectedId,
  label,
  attribution,
  onSelect,
  onHover,
  controls,
}: OsmMapProps) {
  const atlas = useMemo(() => buildBoundaryAtlas(regions), [regions])
  const map = useOsmMap({ atlas, stepOf, selectedId, onSelect, onHover })
  const zoom = useMemo(() => controls(map.controls), [controls, map.controls])
  return (
    <div className={styles.frame}>
      <div
        ref={map.container}
        className={styles.map}
        role="application"
        aria-label={label}
        data-map-surface
      />
      <a
        className={styles.attribution}
        href={__OSM_COPYRIGHT_URL__}
        target="_blank"
        rel="noreferrer"
      >
        {attribution}
      </a>
      {zoom}
    </div>
  )
})
