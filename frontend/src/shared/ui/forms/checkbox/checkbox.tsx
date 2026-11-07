import { clsx } from "clsx"
import styles from "./checkbox.module.css"

export interface CheckboxProps {
  readonly label: string
  readonly checked: boolean
  readonly onChange: (checked: boolean) => void
  readonly disabled?: boolean
  readonly hideLabel?: boolean
  readonly className?: string | undefined
}

export function Checkbox({
  label,
  checked,
  onChange,
  disabled = false,
  hideLabel = false,
  className,
}: CheckboxProps) {
  return (
    <label className={clsx(styles.checkbox, className)} data-disabled={disabled}>
      <input
        type="checkbox"
        className="visually-hidden"
        checked={checked}
        disabled={disabled}
        onChange={(event) => onChange(event.currentTarget.checked)}
      />
      <span className={styles.box} aria-hidden="true">
        <svg className={styles.tick} viewBox="0 0 16 16" focusable="false" aria-hidden="true">
          <path d="M3.5 8.5 6.5 11.5 12.5 4.5" pathLength={1} />
        </svg>
      </span>
      <span className={hideLabel ? "visually-hidden" : styles.label}>{label}</span>
    </label>
  )
}
