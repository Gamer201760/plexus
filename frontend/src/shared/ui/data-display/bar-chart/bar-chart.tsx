import { clsx } from "clsx"
import type { CSSProperties, ReactNode } from "react"
import styles from "./bar-chart.module.css"

export type SeriesSlot = 1 | 2 | 3 | 4

export interface BarChartItem {
  readonly key: string
  readonly label: ReactNode
  readonly display: ReactNode
  readonly value: number | null
  readonly series?: SeriesSlot
}

export interface BarChartProps {
  readonly items: readonly BarChartItem[]
  readonly label: string
  readonly max?: number
  readonly swatches?: boolean
  readonly className?: string | undefined
}

function topValue(items: readonly BarChartItem[], max: number | undefined): number {
  if (max !== undefined && max > 0) return max
  const highest = Math.max(...items.map((item) => item.value ?? 0))
  return highest > 0 ? highest : 1
}

export function BarChart({ items, label, max, swatches = false, className }: BarChartProps) {
  const top = topValue(items, max)
  return (
    <ul className={clsx(styles.chart, className)} aria-label={label}>
      {items.map((item, index) => (
        <li
          key={item.key}
          className={styles.row}
          data-series={item.series ?? 1}
          style={{ "--i": index } as CSSProperties}
        >
          <span className={styles.label}>
            {swatches ? <i className={styles.dot} aria-hidden="true" /> : null}
            {item.label}
          </span>
          <span className={styles.value}>{item.display}</span>
          {item.value === null ? null : (
            <span
              className={styles.bar}
              style={{ "--ratio": Math.max(0, item.value) / top } as CSSProperties}
              aria-hidden="true"
            />
          )}
        </li>
      ))}
    </ul>
  )
}
