import { clsx } from "clsx"
import type { CSSProperties } from "react"
import styles from "./rank-strip.module.css"

export interface RankStripProps {
  readonly values: readonly number[]
  readonly current: number
  readonly label: string
  readonly lowLabel: string
  readonly highLabel: string
  readonly className?: string | undefined
}

function position(value: number, min: number, max: number): number {
  if (max <= min) return 0.5
  return (value - min) / (max - min)
}

function dotKeys(values: readonly number[]): readonly [string, number][] {
  const seen = new Map<number, number>()
  return values.map((value) => {
    const count = seen.get(value) ?? 0
    seen.set(value, count + 1)
    return [`${value}-${count}`, value]
  })
}

export function RankStrip({
  values,
  current,
  label,
  lowLabel,
  highLabel,
  className,
}: RankStripProps) {
  const min = Math.min(current, ...values)
  const max = Math.max(current, ...values)
  return (
    <figure className={clsx(styles.strip, className)}>
      <figcaption className="visually-hidden">{label}</figcaption>
      <span className={styles.track} aria-hidden="true">
        {dotKeys(values).map(([key, value]) => (
          <i
            key={key}
            className={styles.dot}
            style={{ "--x": position(value, min, max) } as CSSProperties}
          />
        ))}
        <i
          className={clsx(styles.dot, styles.marker)}
          style={{ "--x": position(current, min, max) } as CSSProperties}
        />
      </span>
      <span className={styles.ends} aria-hidden="true">
        <span>{lowLabel}</span>
        <span>{highLabel}</span>
      </span>
    </figure>
  )
}
