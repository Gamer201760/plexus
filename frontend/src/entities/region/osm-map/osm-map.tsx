import type { FeatureCollection, LineString } from "geojson"
import { memo, type ReactNode, useMemo } from "react"
import type { AirportCatalog } from "@/shared/api/airports"
import type { ChatMapCommand } from "@/shared/api/chat-map"
import type { RoadLayerProps } from "@/shared/api/road-graph"
import { buildBoundaryAtlas, type RegionBoundary } from "./boundary-geojson"
import styles from "./osm-map.module.css"
import { type MapControls, useOsmMap } from "./use-osm-map"

export interface OsmMapProps {
  readonly airports?: AirportCatalog | undefined
  readonly transit: FeatureCollection<LineString>
  readonly roads?: RoadLayerProps | undefined
  readonly regions: readonly RegionBoundary[]
  readonly stepOf: (id: string) => number
  readonly command?: ChatMapCommand | null
  readonly selectedId: string | null
  readonly label: string
  readonly attribution: string
  readonly onSelect: (id: string) => void
  readonly onHover: (id: string | null, x: number, y: number) => void
  readonly controls: (controls: MapControls) => ReactNode
}

export const OsmMap = memo(function OsmMap({
  airports,
  transit,
  roads,
  regions,
  stepOf,
  selectedId,
  command,
  label,
  attribution,
  onSelect,
  onHover,
  controls,
}: OsmMapProps) {
  const atlas = useMemo(() => buildBoundaryAtlas(regions), [regions])
  const map = useOsmMap({
    airports,
    transit,
    roads,
    atlas,
    stepOf,
    selectedId,
    command,
    onSelect,
    onHover,
  })
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
