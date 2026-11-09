import { clsx } from "clsx"
import type { CSSProperties, ReactNode } from "react"
import styles from "./paired-bars.module.css"

export interface PairedBarsRow {
  readonly key: string
  readonly label: ReactNode
  readonly main: number
  readonly alt: number
  readonly displayMain: string
  readonly displayAlt: string
}

export interface PairedBarsProps {
  readonly rows: readonly PairedBarsRow[]
  readonly label: string
  readonly legendMain: ReactNode
  readonly legendAlt: ReactNode
  readonly className?: string | undefined
}

export function PairedBars({ rows, label, legendMain, legendAlt, className }: PairedBarsProps) {
  const top = Math.max(1, ...rows.flatMap((row) => [row.main, row.alt]))
  return (
    <div className={clsx(styles.chart, className)}>
      <div className={styles.legend}>
        <span className={styles.legendItem} data-pair="main">
          {legendMain}
        </span>
        <span className={styles.legendItem} data-pair="alt">
          {legendAlt}
        </span>
      </div>
      <ul className={styles.rows} aria-label={label}>
        {rows.map((row, index) => (
          <li key={row.key} className={styles.row} style={{ "--i": index } as CSSProperties}>
            <span className={styles.rowLabel}>{row.label}</span>
            <span className={styles.track}>
              <span
                className={styles.bar}
                data-pair="main"
                style={{ "--ratio": row.main / top } as CSSProperties}
                aria-hidden="true"
              />
              <span className={styles.trackValue}>{row.displayMain}</span>
            </span>
            <span className={styles.track}>
              <span
                className={styles.bar}
                data-pair="alt"
                style={{ "--ratio": row.alt / top } as CSSProperties}
                aria-hidden="true"
              />
              <span className={styles.trackValue}>{row.displayAlt}</span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
