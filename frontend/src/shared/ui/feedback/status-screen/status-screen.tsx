import clsx from "clsx"
import type { ReactNode } from "react"
import styles from "./status-screen.module.css"

export type StatusScreenLayout = "split" | "center"

export interface StatusScreenProps {
  readonly art: ReactNode
  readonly title: string
  readonly description: string
  readonly actions?: ReactNode
  readonly layout?: StatusScreenLayout
  readonly children?: ReactNode
  readonly className?: string | undefined
}

export function StatusScreen({
  art,
  title,
  description,
  actions,
  layout = "split",
  children,
  className,
}: StatusScreenProps) {
  return (
    <section className={clsx(styles.screen, layout === "center" && styles.center, className)}>
      <div className={styles.art}>{art}</div>
      <div className={styles.copy}>
        <h1 className={styles.title}>{title}</h1>
        <p className={styles.description}>{description}</p>
        {children}
        {actions === undefined ? null : <div className={styles.actions}>{actions}</div>}
      </div>
    </section>
  )
}
