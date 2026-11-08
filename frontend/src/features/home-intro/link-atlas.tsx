import clsx from "clsx"
import { type CSSProperties, useMemo, useState } from "react"
import type { GeoRegions, Route } from "@/entities/region"
import { buildScene, type Hub } from "./atlas-scene"
import styles from "./link-atlas.module.css"
import { useHubTour } from "./use-hub-tour"

export interface LinkAtlasProps {
  readonly geo: GeoRegions
  readonly routes: readonly Route[]
  readonly label: string
}

interface Frame {
  readonly width: number
  readonly height: number
}

const RIPPLES = [0, 1] as const

function frameOf(viewBox: string): Frame {
  const [, , width = 1, height = 1] = viewBox.split(/\s+/).map(Number)
  return { width, height }
}

function HubFocus({ hub }: { readonly hub: Hub }) {
  return (
    <g>
      {RIPPLES.map((ring) => (
        <circle
          key={ring}
          className={clsx(styles.line, styles.ripple)}
          cx={hub.x}
          cy={hub.y}
          style={{ "--i": ring } as CSSProperties}
        />
      ))}
      {hub.routes.map((route) => (
        <path
          key={route.id}
          className={clsx(styles.line, styles.lit)}
          d={route.path}
          pathLength={1}
        />
      ))}
      {hub.stations.map((station) => (
        <circle
          key={`${station.x}:${station.y}`}
          className={styles.station}
          cx={station.x}
          cy={station.y}
        />
      ))}
    </g>
  )
}

export function LinkAtlas({ geo, routes, label }: LinkAtlasProps) {
  const frame = frameOf(geo.view_box)
  const scene = useMemo(() => buildScene(routes, frame.width), [routes, frame.width])
  const [paused, setPaused] = useState(false)
  const active = useHubTour(scene.hubs.length, paused)
  const hub = active === null ? null : (scene.hubs[active] ?? null)

  return (
    <div
      className={styles.atlas}
      onPointerEnter={() => setPaused(true)}
      onPointerLeave={() => setPaused(false)}
    >
      <svg className={styles.base} viewBox={geo.view_box} role="img" aria-label={label}>
        <g>
          {geo.regions.map((region) => (
            <path key={region.id} className={styles.region} d={region.path_low ?? region.path} />
          ))}
        </g>
        <g>
          {scene.stops.map((stop) => (
            <circle
              key={stop.id}
              className={styles.stop}
              cx={stop.x}
              cy={stop.y}
              style={{ "--sweep": stop.sweep } as CSSProperties}
            />
          ))}
        </g>
      </svg>
      <svg className={styles.overlay} viewBox={geo.view_box} aria-hidden="true">
        {hub ? <HubFocus key={hub.id} hub={hub} /> : null}
        {scene.hubs.map((item) => (
          <circle
            key={item.id}
            className={styles.hub}
            data-active={item.id === hub?.id || undefined}
            cx={item.x}
            cy={item.y}
          />
        ))}
      </svg>
      {hub ? (
        <div
          key={hub.id}
          className={styles.label}
          data-hub-label
          data-below={hub.below || undefined}
          style={
            {
              "--x": hub.x / frame.width,
              "--y": hub.y / frame.height,
            } as CSSProperties
          }
        >
          {hub.name}
        </div>
      ) : null}
    </div>
  )
}
