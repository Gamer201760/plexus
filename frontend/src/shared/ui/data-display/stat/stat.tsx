import { clsx } from "clsx"
import type { ReactNode } from "react"
import { Icon, type IconName } from "../../primitives/icon/icon"
import styles from "./stat.module.css"

export type StatTrend = "up" | "down" | "flat"
export type StatTone = "gain" | "loss" | "neutral"

export interface StatDelta {
  readonly value: string
  readonly trend: StatTrend
  readonly tone?: StatTone
  readonly label?: string | undefined
}

export interface StatProps {
  readonly label: string
  readonly value: ReactNode
  readonly unit?: string | undefined
  readonly delta?: StatDelta | undefined
  readonly className?: string | undefined
}

const TREND_ICON: Readonly<Record<StatTrend, IconName | null>> = {
  up: "arrow-up",
  down: "arrow-down",
  flat: null,
}

const TONE_CLASS: Readonly<Record<StatTone, string | undefined>> = {
  gain: styles.gain,
  loss: styles.loss,
  neutral: styles.neutral,
}

function Delta({ value, trend, tone = "neutral", label }: StatDelta) {
  const icon = TREND_ICON[trend]
  return (
    <span className={clsx(styles.delta, TONE_CLASS[tone])} data-trend={trend}>
      {icon === null ? null : <Icon name={icon} size="sm" />}
      <span>{value}</span>
      {label === undefined ? null : <span className={styles.deltaLabel}>{label}</span>}
    </span>
  )
}

export function Stat({ label, value, unit, delta, className }: StatProps) {
  return (
    <div className={clsx(styles.stat, className)}>
      <span className={styles.label}>{label}</span>
      <span className={styles.value}>
        <span className={styles.number}>{value}</span>
        {unit === undefined ? null : <span className={styles.unit}>{unit}</span>}
      </span>
      {delta === undefined ? null : <Delta {...delta} />}
    </div>
  )
}
