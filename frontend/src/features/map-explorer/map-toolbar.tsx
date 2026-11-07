import type { Season } from "@/entities/region"
import { useTranslation } from "@/shared/i18n"
import { Segmented, Select } from "@/shared/ui"
import styles from "./map-explorer.module.css"
import { METRICS, type MetricKey } from "./metric"

export interface MapToolbarProps {
  readonly metric: MetricKey
  readonly season: Season
  readonly onMetric: (metric: MetricKey) => void
  readonly onSeason: (season: Season) => void
}

export function MapToolbar({ metric, season, onMetric, onSeason }: MapToolbarProps) {
  const { t } = useTranslation()
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
      <Segmented
        label={t("data:season.legend")}
        value={season}
        onChange={onSeason}
        options={(["all", "summer", "winter"] as const).map((key) => ({
          value: key,
          label: t(`data:seasonShort.${key}`),
        }))}
      />
    </div>
  )
}
