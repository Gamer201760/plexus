import type { CSSProperties } from "react"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Icon } from "@/shared/ui"
import styles from "./season-pair.module.css"
export interface SeasonPairProps {
  readonly summer: number
  readonly winter: number
  readonly compact?: boolean
}
export function SeasonPair({ summer, winter, compact = false }: SeasonPairProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  return (
    <div className={styles.pair} data-compact={compact}>
      {(["summer", "winter"] as const).map((key) => (
        <div key={key}>
          <span>
            <Icon name={key === "summer" ? "sun" : "snowflake"} size="sm" />
            {compact ? null : t(`data:season.${key}`)}
          </span>
          {compact ? (
            <i
              data-season={key}
              style={
                {
                  "--bar-ratio": (key === "summer" ? summer : winter) / Math.max(1, summer, winter),
                } as CSSProperties
              }
            />
          ) : null}
          <strong>{f.integer(key === "summer" ? summer : winter)}</strong>
        </div>
      ))}
    </div>
  )
}
