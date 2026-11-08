import type { Season } from "@/entities/region"
import { useTranslation } from "@/shared/i18n"
import { Segmented, Select, Tooltip } from "@/shared/ui"
import styles from "./map-explorer.module.css"
import { dependsOnSeason, METRICS, type MetricKey, SEASONS } from "./metric"

export interface MapToolbarProps {
  readonly metric: MetricKey
  readonly season: Season
  readonly onMetric: (metric: MetricKey) => void
  readonly onSeason: (season: Season) => void
}

export function MapToolbar({ metric, season, onMetric, onSeason }: MapToolbarProps) {
  const { t } = useTranslation()
  const seasonal = dependsOnSeason(metric)
  const seasons = (
    <Segmented
      label={t("data:season.legend")}
      value={season}
      onChange={onSeason}
      options={SEASONS.map((key) => ({ value: key, label: t(`data:seasonShort.${key}`) }))}
    />
  )
  return (
    <div className={styles.toolbar}>
      <Select
        label={t("data:metric.label")}
        hideLabel
        value={metric}
        onChange={onMetric}
        options={METRICS.map((key) => ({ value: key, label: t(`data:metric.${key}`) }))}
        className={styles.metric}
      />
      {seasonal ? (
        seasons
      ) : (
        <Tooltip content={t("map:seasonIgnored")} side="bottom">
          <fieldset className={styles.seasonOff} disabled>
            {seasons}
          </fieldset>
        </Tooltip>
      )}
    </div>
  )
}
