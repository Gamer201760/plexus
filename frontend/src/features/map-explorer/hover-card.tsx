import type { CSSProperties } from "react"
import styles from "./hover-card.module.css"

export interface HoverCardProps {
  readonly x: number
  readonly y: number
  readonly title: string
  readonly label: string
  readonly value: string | null
  readonly none: string
}

export function HoverCard({ x, y, title, label, value, none }: HoverCardProps) {
  return (
    <div
      className={styles.hover}
      style={{ "--hover-x": `${x}px`, "--hover-y": `${y}px` } as CSSProperties}
      aria-hidden="true"
    >
      <b className={styles.hoverTitle}>{title}</b>
      <span className={styles.hoverRow}>
        <span>{label}</span>
        <span className={styles.hoverValue}>{value ?? none}</span>
      </span>
    </div>
  )
}
