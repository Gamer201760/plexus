import { clsx } from "clsx"
import type { ReactNode } from "react"
import { Icon, type IconName } from "../../primitives/icon/icon"
import { type StatusTone, TONE_CLASS, TONE_ICON } from "../status-badge/status-badge"
import styles from "./banner.module.css"

export interface BannerProps {
  readonly tone: StatusTone
  readonly title: string
  readonly description?: ReactNode
  readonly action?: ReactNode
  readonly icon?: IconName | undefined
  readonly announce?: boolean
  readonly className?: string | undefined
}

export function Banner({
  tone,
  title,
  description,
  action,
  icon,
  announce = false,
  className,
}: BannerProps) {
  const role = tone === "danger" ? "alert" : "status"
  return (
    <div
      className={clsx(styles.banner, TONE_CLASS[tone], className)}
      role={announce ? role : undefined}
      data-tone={tone}
    >
      <Icon name={icon ?? TONE_ICON[tone]} size="md" className={styles.icon} />
      <div className={styles.text}>
        <p className={styles.title}>{title}</p>
        {description === undefined ? null : <p className={styles.description}>{description}</p>}
      </div>
      {action === undefined ? null : <div className={styles.action}>{action}</div>}
    </div>
  )
}
