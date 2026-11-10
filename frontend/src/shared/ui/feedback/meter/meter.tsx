import styles from "./meter.module.css"

export interface MeterProps {
  readonly value: number
  readonly max: number
  readonly label: string
}

export function Meter({ value, max, label }: MeterProps) {
  return <progress className={styles.meter} value={value} max={max} aria-label={label} />
}
