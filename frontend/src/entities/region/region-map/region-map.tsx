import clsx from "clsx"
import type { CSSProperties } from "react"
import styles from "./region-map.module.css"
import {
  ACTIVE_ENDPOINT_SCALE,
  baseRadius,
  ENDPOINT_SCALE,
  isDrawable,
  linkEndpoints,
  type MapLink,
  type MapSettlement,
  placeRadius,
  presentModes,
} from "./region-map-geometry"
import { RegionMapLegend } from "./region-map-legend"

export interface RegionMapProps {
  readonly path: string
  readonly bbox: readonly number[]
  readonly settlements: readonly MapSettlement[]
  readonly links: readonly MapLink[]
  readonly activeLinkId: string | null
  readonly highlightId: string | null
  readonly label: string
  readonly onLink: (id: string) => void
}

const PAD = 0.08

interface FocusProps {
  readonly place: MapSettlement
  readonly span: number
}

function Focus({ place, span }: FocusProps) {
  if (place.x === null || place.y === null) return null
  const r = placeRadius(place.population, span)
  return (
    <g className={styles.focus} style={{ "--r": r } as CSSProperties}>
      {[3, 2, 1].map((k) => (
        <circle
          key={k}
          className={styles.ring}
          data-ring={k}
          cx={place.x ?? 0}
          cy={place.y ?? 0}
          r={r * (1 + k * 1.6)}
        />
      ))}
      <circle className={styles.placeFocus} cx={place.x} cy={place.y} r={r * 1.4} />
    </g>
  )
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
  const drawable = links.filter(isDrawable)
  const ordered = [...drawable].sort(
    (a, b) => Number(a.id === activeLinkId) - Number(b.id === activeLinkId),
  )
  const focused = drawable.some((link) => link.id === activeLinkId)
  const ends = linkEndpoints(drawable, activeLinkId)
  const highlighted = settlements.find((s) => s.id === highlightId)
  const base = baseRadius(span)
  return (
    <figure className={styles.frame}>
      <svg
        className={styles.map}
        viewBox={viewBox}
        role="img"
        aria-label={label}
        data-focused={focused || undefined}
      >
        <path className={styles.land} d={path} />
        {settlements.map((s) =>
          s.x === null || s.y === null ? null : (
            <circle
              key={s.id}
              className={styles.place}
              cx={s.x}
              cy={s.y}
              r={placeRadius(s.population, span)}
            />
          ),
        )}
        {ordered.map((link) => (
          // biome-ignore lint/a11y/noStaticElementInteractions: links on the map mirror the keyboard-accessible list beside it
          <line
            key={link.id}
            className={clsx(styles.toned, styles.link, link.id === activeLinkId && styles.active)}
            data-mode={link.mode}
            data-season={link.season ?? "unknown"}
            x1={link.from.x ?? 0}
            y1={link.from.y ?? 0}
            x2={link.to.x ?? 0}
            y2={link.to.y ?? 0}
            onClick={() => onLink(link.id)}
          />
        ))}
        {ends.map((end) => (
          <circle
            key={end.key}
            className={clsx(styles.toned, styles.end, end.active && styles.endActive)}
            data-mode={end.mode}
            cx={end.x}
            cy={end.y}
            r={base * (end.active ? ACTIVE_ENDPOINT_SCALE : ENDPOINT_SCALE)}
          />
        ))}
        {highlighted ? <Focus place={highlighted} span={span} /> : null}
      </svg>
      <RegionMapLegend modes={presentModes(drawable)} links={drawable} />
    </figure>
  )
}
