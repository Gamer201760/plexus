import clsx from "clsx"
import type { CSSProperties } from "react"
import type { components } from "@/shared/api"
import styles from "./region-map.module.css"

type Link = components["schemas"]["LinkResponse"]
type Settlement = components["schemas"]["SettlementResponse"]

export interface RegionMapProps {
  readonly path: string
  readonly bbox: readonly number[]
  readonly settlements: readonly Settlement[]
  readonly links: readonly Link[]
  readonly activeLinkId: string | null
  readonly highlightId: string | null
  readonly label: string
  readonly onLink: (id: string) => void
}

const PAD = 0.08

function radius(population: number | null, span: number) {
  const base = span / 260
  if (population === null) return base
  return base * (0.7 + Math.min(Math.sqrt(population) / 60, 4))
}

export function RegionMap({
  path,
  bbox,
  settlements,
  links,
  activeLinkId,
  highlightId,
  label,
  onLink,
}: RegionMapProps) {
  const [x = 0, y = 0, w = 1, h = 1] = bbox
  const span = Math.max(w, h)
  const pad = span * PAD
  const viewBox = `${x - pad} ${y - pad} ${w + pad * 2} ${h + pad * 2}`
  const drawable = links.filter(
    (link) =>
      link.from.x !== null && link.from.y !== null && link.to.x !== null && link.to.y !== null,
  )
  const highlighted = settlements.find((s) => s.id === highlightId)
  return (
    <svg className={styles.map} viewBox={viewBox} role="img" aria-label={label}>
      <path className={styles.land} d={path} />
      {drawable.map((link) => (
        // biome-ignore lint/a11y/noStaticElementInteractions: links on the map mirror the keyboard-accessible list beside it
        <line
          key={link.id}
          className={clsx(styles.link, link.id === activeLinkId && styles.active)}
          data-mode={link.mode}
          data-season={link.season ?? "unknown"}
          x1={link.from.x ?? 0}
          y1={link.from.y ?? 0}
          x2={link.to.x ?? 0}
          y2={link.to.y ?? 0}
          onClick={() => onLink(link.id)}
        />
      ))}
      {settlements.map((s) =>
        s.x === null || s.y === null ? null : (
          <circle
            key={s.id}
            className={styles.place}
            cx={s.x}
            cy={s.y}
            r={radius(s.population, span)}
          />
        ),
      )}
      {highlighted && highlighted.x !== null && highlighted.y !== null ? (
        <g
          className={styles.focus}
          style={{ "--r": radius(highlighted.population, span) } as CSSProperties}
        >
          {[3, 2, 1].map((k) => (
            <circle
              key={k}
              className={styles.ring}
              data-ring={k}
              cx={highlighted.x ?? 0}
              cy={highlighted.y ?? 0}
              r={radius(highlighted.population, span) * (1 + k * 1.6)}
            />
          ))}
          <circle
            className={styles.placeFocus}
            cx={highlighted.x}
            cy={highlighted.y}
            r={radius(highlighted.population, span) * 1.4}
          />
        </g>
      ) : null}
    </svg>
  )
}
