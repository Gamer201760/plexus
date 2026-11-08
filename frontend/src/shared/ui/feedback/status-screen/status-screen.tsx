import clsx from "clsx"
import type { ReactNode } from "react"
import styles from "./status-screen.module.css"

export interface StatusScreenProps {
  readonly art: ReactNode
  readonly title: string
  readonly description: string
  readonly actions: ReactNode
  readonly children?: ReactNode
  readonly className?: string | undefined
}

export function StatusScreen({
  art,
  title,
  description,
  actions,
  children,
  className,
}: StatusScreenProps) {
  return (
    <section className={clsx(styles.screen, className)}>
      <div className={styles.art}>{art}</div>
      <div className={styles.copy}>
        <h1 className={styles.title}>{title}</h1>
        <p className={styles.description}>{description}</p>
        {children}
        <div className={styles.actions}>{actions}</div>
      </div>
    </section>
  )
}
