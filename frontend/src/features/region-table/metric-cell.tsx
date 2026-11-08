import type { CSSProperties, ReactNode } from "react"
import styles from "./metric-cell.module.css"

export interface MetricCellProps {
  readonly value: number | null
  readonly max: number
  readonly bar: boolean
  readonly children: ReactNode
}

export function MetricCell({ value, max, bar, children }: MetricCellProps) {
  if (!bar) return children
  const ratio = value === null || max <= 0 ? 0 : Math.max(0, value) / max
  return (
    <span className={styles.cell}>
      <span className={styles.track} aria-hidden="true">
        <span className={styles.bar} style={{ "--v": ratio } as CSSProperties} />
      </span>
      <span>{children}</span>
    </span>
  )
}
