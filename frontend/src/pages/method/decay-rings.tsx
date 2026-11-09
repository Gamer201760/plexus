import type { CSSProperties } from "react"
import { useFormatters, useTranslation } from "@/shared/i18n"
import styles from "./decay-rings.module.css"

const RADII = [56, 94, 132] as const
const WEIGHTS = ["½", "¼", "⅛"] as const

export interface DecayRingsProps {
  readonly halfLife: number
  readonly className?: string | undefined
}

export function DecayRings({ halfLife, className }: DecayRingsProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  return (
    <figure className={className}>
      <svg className={styles.art} viewBox="0 0 320 320" aria-hidden="true">
        {RADII.map((radius, index) => (
          <circle
            key={radius}
            className={styles.ring}
            data-ring={index + 1}
            style={{ "--i": index } as CSSProperties}
            cx="160"
            cy="160"
            r={radius}
            vectorEffect="non-scaling-stroke"
          />
        ))}
        <circle className={styles.origin} cx="160" cy="160" r="4" />
        {RADII.map((radius, index) => (
          <text key={radius} className={styles.label} x="160" y={160 - radius + 18}>
            {t("method:decay.ring", {
              hours: f.integer(halfLife * (index + 1)),
              weight: WEIGHTS[index],
            })}
          </text>
        ))}
      </svg>
      <figcaption className={styles.caption}>
        {t("method:decay.caption", { value: halfLife })}
      </figcaption>
    </figure>
  )
}
