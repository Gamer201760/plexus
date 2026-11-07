import { clsx } from "clsx"
import styles from "./switch.module.css"

export interface SwitchProps {
  readonly label: string
  readonly checked: boolean
  readonly onChange: (checked: boolean) => void
  readonly disabled?: boolean
  readonly hideLabel?: boolean
  readonly className?: string | undefined
}

export function Switch({
  label,
  checked,
  onChange,
  disabled = false,
  hideLabel = false,
  className,
}: SwitchProps) {
  return (
    <label className={clsx(styles.switch, className)} data-disabled={disabled}>
      <input
        type="checkbox"
        role="switch"
        aria-checked={checked}
        className="visually-hidden"
        checked={checked}
        disabled={disabled}
        onChange={(event) => onChange(event.currentTarget.checked)}
      />
      <span className={styles.track} aria-hidden="true">
        <span className={styles.thumb} />
      </span>
      <span className={hideLabel ? "visually-hidden" : styles.label}>{label}</span>
    </label>
  )
}
