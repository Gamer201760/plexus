import { clsx } from "clsx"
import { Icon, type IconName } from "../../primitives/icon/icon"
import styles from "./status-badge.module.css"

export type StatusTone = "neutral" | "info" | "success" | "warning" | "danger"

export const TONE_ICON: Readonly<Record<StatusTone, IconName>> = {
  neutral: "neutral",
  info: "info",
  success: "success",
  warning: "alert",
  danger: "danger",
}

export const TONE_CLASS: Readonly<Record<StatusTone, string | undefined>> = {
  neutral: styles.neutral,
  info: styles.info,
  success: styles.success,
  warning: styles.warning,
  danger: styles.danger,
}

export interface StatusBadgeProps {
  readonly tone: StatusTone
  readonly label: string
  readonly icon?: IconName | undefined
  readonly className?: string | undefined
}

export function StatusBadge({ tone, label, icon, className }: StatusBadgeProps) {
  return (
    <span className={clsx(styles.badge, TONE_CLASS[tone], className)} data-tone={tone}>
      <Icon name={icon ?? TONE_ICON[tone]} size="sm" className={styles.icon} />
      <span>{label}</span>
    </span>
  )
}
