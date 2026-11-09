import { type RefObject, useLayoutEffect } from "react"
import styles from "./hover-card.module.css"

export interface HoverCardProps {
  readonly cardRef: RefObject<HTMLDivElement | null>
  readonly point: RefObject<{ x: number; y: number }>
  readonly title: string
  readonly label: string
  readonly value: string | null
  readonly none: string
}

export function HoverCard({ cardRef, point, title, label, value, none }: HoverCardProps) {
  useLayoutEffect(() => {
    if (cardRef.current)
      cardRef.current.style.transform = `translate(${point.current.x}px, ${point.current.y}px)`
  }, [cardRef, point])
  return (
    <div className={styles.hover} ref={cardRef} aria-hidden="true">
      <b className={styles.hoverTitle}>{title}</b>
      <span className={styles.hoverRow}>
        <span>{label}</span>
        <span className={styles.hoverValue}>{value ?? none}</span>
      </span>
    </div>
  )
}
