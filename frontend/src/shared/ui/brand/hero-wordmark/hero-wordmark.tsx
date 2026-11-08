import type { CSSProperties } from "react"
import { useTranslation } from "@/shared/i18n"
import styles from "./hero-wordmark.module.css"
import letters from "./letters.json"

export function HeroWordmark() {
  const { t } = useTranslation()
  return (
    <div className={styles.wordmark} role="img" aria-label={t("common:app.name")}>
      {letters.map(({ left, right, path }, index) => (
        <span
          key={left}
          className={styles.letter}
          aria-hidden="true"
          style={
            {
              "--letter-left": `${(left / 228) * 100}%`,
              "--letter-width": `${((right - left) / 228) * 100}%`,
              "--i": index,
            } as CSSProperties
          }
        >
          <svg viewBox={`${left} -56 ${right - left} 73`} aria-hidden="true">
            <path d={path} fillRule="evenodd" />
          </svg>
        </span>
      ))}
    </div>
  )
}
