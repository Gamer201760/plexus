import clsx from "clsx"
import { type CSSProperties, type ReactNode, useId } from "react"
import styles from "./selection-rings.module.css"
import type { Box } from "./use-map-view"

export interface SelectionRingsProps {
  readonly path: string
  readonly frame: Box
  readonly unit: number
  readonly children: ReactNode
}

interface OuterRing {
  readonly order: number
  readonly outer: string | undefined
  readonly inner: string | undefined
  readonly line: string | undefined
}

const OUTER_RINGS: readonly OuterRing[] = [
  { order: 2, outer: styles.outer3, inner: styles.inner3, line: styles.ring3 },
  { order: 1, outer: styles.outer2, inner: styles.inner2, line: styles.ring2 },
]

export function SelectionRings({ path, frame, unit, children }: SelectionRingsProps) {
  const base = useId().replace(/[^\w-]/g, "")
  const bounds = {
    x: frame.x - frame.width,
    y: frame.y - frame.height,
    width: frame.width * 3,
    height: frame.height * 3,
  }
  return (
    <g className={styles.selection} style={{ "--map-unit": unit } as CSSProperties}>
      {OUTER_RINGS.map((ring) => {
        const maskId = `${base}-ring-${ring.order}`
        return (
          <g
            key={ring.order}
            className={styles.enter}
            style={{ "--i": ring.order } as CSSProperties}
            mask={`url(#${maskId})`}
          >
            <mask id={maskId} maskUnits="userSpaceOnUse" {...bounds}>
              <path className={clsx(styles.band, ring.outer)} d={path} />
              <path className={clsx(styles.cut, ring.inner)} d={path} />
            </mask>
            <path className={clsx(styles.line, ring.line)} d={path} />
          </g>
        )
      })}
      {children}
      <path
        className={clsx(styles.enter, styles.line, styles.ring1)}
        style={{ "--i": 0 } as CSSProperties}
        d={path}
      />
    </g>
  )
}
