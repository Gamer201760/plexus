import { useTranslation } from "@/shared/i18n"
import styles from "./map-legend.module.css"
import type { MetricKey } from "./metric"

const STEPS = [1, 2, 3, 4, 5, 6, 7] as const

export interface MapLegendProps {
  readonly metric: MetricKey
}

export function MapLegend({ metric }: MapLegendProps) {
  const { t } = useTranslation()
  return (
    <figure className={styles.legend}>
      <figcaption className={styles.legendTitle}>{t(`data:metric.${metric}`)}</figcaption>
      <div className={styles.ramp} aria-hidden="true">
        {STEPS.map((step) => (
          <span key={step} className={styles.swatch} data-step={step} />
        ))}
      </div>
      <div className={styles.rampScale}>
        <span>{t("map:legend.less")}</span>
        <span>{t("map:legend.more")}</span>
      </div>
      <div className={styles.legendNone}>
        <span className={styles.swatch} data-step={0} aria-hidden="true" />
        <span>{t("map:legend.none")}</span>
      </div>
    </figure>
  )
}
