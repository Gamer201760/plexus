import { clsx } from "clsx"
import { type InputHTMLAttributes, type Ref, useId } from "react"
import { Icon, type IconName } from "../../primitives/icon/icon"
import styles from "./text-field.module.css"

export type TextFieldType = "text" | "search" | "email" | "tel" | "url" | "password"

export interface TextFieldProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, "prefix" | "size" | "type" | "children"> {
  readonly label: string
  readonly hideLabel?: boolean
  readonly type?: TextFieldType
  readonly icon?: IconName | undefined
  readonly suffix?: string | undefined
  readonly hint?: string | undefined
  readonly error?: string | undefined
  readonly ref?: Ref<HTMLInputElement> | undefined
  readonly boxRef?: Ref<HTMLDivElement> | undefined
}

export function TextField({
  label,
  hideLabel = false,
  type = "text",
  icon,
  suffix,
  hint,
  error,
  boxRef,
  id,
  className,
  "aria-describedby": describedBy,
  ...rest
}: TextFieldProps) {
  const ownId = useId()
  const inputId = id ?? ownId
  const messageId = useId()
  const message = error ?? hint
  const invalid = error !== undefined
  const describers = [describedBy, message === undefined ? undefined : messageId].filter(Boolean)
  return (
    <div className={clsx(styles.field, className)}>
      <label htmlFor={inputId} className={hideLabel ? "visually-hidden" : styles.label}>
        {label}
      </label>
      <div ref={boxRef} className={styles.box} data-invalid={invalid}>
        {icon === undefined ? null : <Icon name={icon} size="sm" className={styles.icon} />}
        <input
          {...rest}
          id={inputId}
          type={type}
          className={styles.input}
          aria-invalid={invalid || undefined}
          aria-describedby={describers.length === 0 ? undefined : describers.join(" ")}
        />
        {suffix === undefined ? null : <span className={styles.suffix}>{suffix}</span>}
      </div>
      {message === undefined ? null : (
        <p id={messageId} className={clsx(styles.message, invalid && styles.error)}>
          {invalid ? <Icon name="error" size="sm" className={styles.messageIcon} /> : null}
          <span>{message}</span>
        </p>
      )}
    </div>
  )
}
