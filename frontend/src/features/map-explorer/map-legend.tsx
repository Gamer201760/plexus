import clsx from "clsx"
import { memo, type ReactNode } from "react"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Button, Checkbox, Skeleton } from "@/shared/ui"
import { TransportIcon } from "@/shared/ui/brand"
import { formatThreshold } from "./format-metric"
import styles from "./map-legend.module.css"
import type { MetricKey } from "./metric"
import type { MetricScale } from "./scale"

export interface MapLegendProps {
  readonly metric: MetricKey
  readonly scale: MetricScale
  readonly missing: boolean
  readonly children?: ReactNode
}

export const MapLegend = memo(function MapLegend({
  metric,
  scale,
  missing,
  children,
}: MapLegendProps) {
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
      {children}
    </figure>
  )
})

interface TransitLegendProps {
  readonly selectedId: string | null
  readonly loading: boolean
  readonly failed: boolean
  readonly empty: boolean
  readonly missing: number
  readonly modelCount: number
  readonly showModels: boolean
  readonly onModelsChange: (value: boolean) => void
  readonly modeled: boolean
  readonly onRetry: () => void
}

export function TransitLegend({
  selectedId,
  loading,
  failed,
  empty,
  missing,
  modeled,
  modelCount,
  showModels,
  onModelsChange,
  onRetry,
}: TransitLegendProps) {
  const { t } = useTranslation()
  if (!selectedId) return null
  if (failed)
    return (
      <div className={styles.transitNote} role="status">
        <p>{t("map:connections.failed")}</p>
        <Button variant="ghost" icon="retry" onClick={onRetry}>
          {t("common:action.retry")}
        </Button>
      </div>
    )
  if (loading) return <Skeleton lines={2} />
  return (
    <div className={styles.transitNote}>
      {!empty ? (
        <div className={styles.transitModes}>
          <span>
            <TransportIcon mode="rail" size="sm" />
            {t("data:mode.rail")}
          </span>
          <span>
            <TransportIcon mode="air" size="sm" />
            {t("data:mode.air")}
          </span>
        </div>
      ) : null}
      {modelCount > 0 ? (
        <Checkbox
          label={t("map:connections.showModels", { count: modelCount })}
          checked={showModels}
          onChange={onModelsChange}
        />
      ) : null}
      <p>{t(empty && modelCount === 0 ? "map:connections.empty" : "map:connections.schematic")}</p>
      {modeled ? <p>{t("map:connections.model")}</p> : null}
      {missing > 0 ? <p>{t("map:connections.missing", { count: missing })}</p> : null}
    </div>
  )
}
