import clsx from "clsx"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { formatThreshold } from "./format-metric"
import styles from "./map-legend.module.css"
import type { MetricKey } from "./metric"
import type { MetricScale } from "./scale"

export interface MapLegendProps {
  readonly metric: MetricKey
  readonly scale: MetricScale
  readonly missing: boolean
}

export function MapLegend({ metric, scale, missing }: MapLegendProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const title = t(`data:metric.${metric}`)
  return (
    <figure className={styles.legend} aria-label={title}>
      <figcaption className={styles.legendTitle} aria-hidden="true">
        {title}
      </figcaption>
      <ol className={styles.scale}>
        {scale.hasZero ? (
          <li className={clsx(styles.bin, styles.zero)}>
            <span className={styles.swatch} data-step={1} aria-hidden="true" />
            <span className={styles.tick}>{formatThreshold(0, metric, f)}</span>
          </li>
        ) : null}
        {scale.bins.map((bin) => {
          const value = formatThreshold(bin.from, metric, f)
          return (
            <li key={bin.step} className={styles.bin}>
              <span className={styles.swatch} data-step={bin.step} aria-hidden="true" />
              <span className={styles.tick} aria-hidden="true">
                {value}
              </span>
              <span className="visually-hidden">{t("map:legend.from", { value })}</span>
            </li>
          )
        })}
      </ol>
      {missing ? (
        <p className={styles.legendNone}>
          <span className={styles.swatch} data-step={0} aria-hidden="true" />
          <span>{t("map:legend.none")}</span>
        </p>
      ) : null}
    </figure>
  )
}
