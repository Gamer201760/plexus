import clsx from "clsx"
import { type DesignIconName, designArtwork } from "../../primitives/icon/design-icon"
import styles from "./transport-icon.module.css"
import type { TransportMode } from "./transport-paths"

export type TransportIconSize = "sm" | "md" | "lg"

const SIZES: Record<TransportIconSize, string | undefined> = {
  sm: styles.sm,
  md: styles.md,
  lg: styles.lg,
}

const TINTS: Record<TransportMode, string | undefined> = {
  bus: undefined,
  air: styles.air,
  river: styles.river,
  winter_road: styles.winter,
  ferry: styles.ferry,
  ice_crossing: styles.winter,
  pontoon_bridge: styles.ferry,
}

export interface TransportIconProps {
  readonly mode: TransportMode
  readonly size?: TransportIconSize
  readonly tinted?: boolean
  readonly className?: string | undefined
}

export function TransportIcon({ mode, size = "md", tinted = true, className }: TransportIconProps) {
  const names: Record<TransportMode, DesignIconName> = {
    bus: "bus",
    air: "air",
    river: "river",
    winter_road: "winter",
    ferry: "ferry",
    ice_crossing: "snow",
    pontoon_bridge: "bridge",
  }
  return (
    <svg
      className={clsx(styles.icon, SIZES[size], tinted && TINTS[mode], className)}
      viewBox="0 0 24 24"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {designArtwork(names[mode])}
    </svg>
  )
}
