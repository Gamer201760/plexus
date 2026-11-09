import { type RefObject, useLayoutEffect } from "react"
import styles from "./hover-card.module.css"

export interface HoverCardRow {
  readonly key: string
  readonly label: string
  readonly value: string | null
}

export interface HoverCardProps {
  readonly cardRef: RefObject<HTMLDivElement | null>
  readonly point: RefObject<{ x: number; y: number }>
  readonly title: string
  readonly rows: readonly HoverCardRow[]
  readonly none: string
}

export function HoverCard({ cardRef, point, title, rows, none }: HoverCardProps) {
  useLayoutEffect(() => {
    if (cardRef.current)
      cardRef.current.style.transform = `translate(${point.current.x}px, ${point.current.y}px)`
  }, [cardRef, point])
  return (
    <div className={styles.hover} ref={cardRef} aria-hidden="true">
      <b className={styles.hoverTitle}>{title}</b>
      {rows.map((row) => (
        <span key={row.key} className={styles.hoverRow}>
          <span>{row.label}</span>
          <span className={styles.hoverValue}>{row.value ?? none}</span>
        </span>
      ))}
    </div>
  )
}
