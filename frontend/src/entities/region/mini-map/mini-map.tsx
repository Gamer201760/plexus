import { useMemo } from "react"
import { type RegionSummary, useGeoRegions } from "../region.queries"
import styles from "./mini-map.module.css"
export interface MiniMapProps {
  readonly rows: readonly RegionSummary[]
  readonly selectedId: string
}
export function MiniMap({ rows, selectedId }: MiniMapProps) {
  const { data } = useGeoRegions()
  const values = useMemo(() => new Map(rows.map((r) => [r.id, r.links_season])), [rows])
  const max = Math.max(1, ...values.values())
  if (!data) return null
  return (
    <svg className={styles.map} viewBox={data.view_box} aria-hidden="true">
      {data.regions.map((r) => (
        <path
          key={r.id}
          d={r.path_low ?? r.path}
          data-selected={r.id === selectedId}
          style={{
            fill: values.get(r.id)
              ? `var(--data-seq-${Math.min(7, 1 + Math.floor((6 * (values.get(r.id) ?? 0)) / max))})`
              : "var(--map-none)",
          }}
        />
      ))}
    </svg>
  )
}
