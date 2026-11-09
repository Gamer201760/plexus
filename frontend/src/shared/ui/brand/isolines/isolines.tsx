import clsx from "clsx"
import type { CSSProperties } from "react"
import { blobPath } from "./iso-path"
import styles from "./isolines.module.css"

export type IsolinesShape = "circle" | "blob"
export type IsolinesMotion = "none" | "enter" | "pulse"

const RADII: Record<1 | 2 | 3, readonly number[]> = {
  1: [44],
  2: [30, 46],
  3: [22, 34, 46],
}

const RING_MOTIONS: Record<IsolinesMotion, string | undefined> = {
  none: undefined,
  enter: styles.ringEnter,
  pulse: styles.ringPulse,
}

export interface IsolinesProps {
  readonly rings?: 1 | 2 | 3
  readonly shape?: IsolinesShape
  readonly seed?: number
  readonly motion?: IsolinesMotion
  readonly className?: string | undefined
}

export function Isolines({
  rings = 3,
  shape = "circle",
  seed = 1,
  motion = "none",
  className,
}: IsolinesProps) {
  const radii = RADII[rings]
  const wobble = shape === "blob" ? 0.1 : 0
  return (
    <svg
      className={clsx(styles.isolines, className)}
      viewBox="0 0 100 100"
      aria-hidden="true"
      preserveAspectRatio="xMidYMid meet"
    >
      {radii.map((radius, index) => (
        <path
          key={radius}
          className={clsx(styles.ring, RING_MOTIONS[motion])}
          data-ring={index + 1}
          style={{ "--i": index } as CSSProperties}
          d={blobPath(50, 50, radius, seed + index * 0.45, wobble)}
          vectorEffect="non-scaling-stroke"
        />
      ))}
    </svg>
  )
}
