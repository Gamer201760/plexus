import clsx from "clsx"
import { memo, type ReactNode, useId, useRef, useState } from "react"
import type { AirportCatalog } from "@/shared/api/airports"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Button, Checkbox, Popover, Skeleton } from "@/shared/ui"
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
            {t("map:connections.railShort")}
          </span>
          <span>
            <TransportIcon mode="air" size="sm" />
            {t("data:mode.air")}
          </span>
        </div>
      ) : null}
      <div className={styles.transitHeader}>
        {modelCount > 0 ? (
          <Checkbox
            label={t("map:connections.showModels", { count: modelCount })}
            checked={showModels}
            onChange={onModelsChange}
          />
        ) : null}
        <LegendHelp
          content={[
            t("map:connections.schematic"),
            modeled ? t("map:connections.model") : "",
            missing > 0 ? t("map:connections.missing", { count: missing }) : "",
          ]
            .filter(Boolean)
            .join(" ")}
        />
      </div>
      {empty && modelCount === 0 ? <p>{t("map:connections.empty")}</p> : null}
    </div>
  )
}

function LegendHelp({ content }: { readonly content: string }) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  const anchor = useRef<HTMLButtonElement>(null)
  const id = useId()
  return (
    <>
      <Button
        ref={anchor}
        variant="ghost"
        icon="info"
        aria-label={t("map:connections.details")}
        aria-expanded={open}
        aria-controls={open ? id : undefined}
        onClick={() => setOpen((value) => !value)}
      >
        {null}
      </Button>
      <Popover
        id={id}
        open={open}
        onClose={() => setOpen(false)}
        anchorRef={anchor}
        side="top"
        align="end"
        label={t("map:connections.details")}
        focusOnOpen
        className={styles.help}
      >
        <p>{content}</p>
      </Popover>
    </>
  )
}

export function AirportLegend({
  catalog,
  failed,
}: {
  readonly catalog: AirportCatalog | undefined
  readonly failed: boolean
}) {
  const { t } = useTranslation()
  const key = failed
    ? "map:airports.failed"
    : catalog
      ? "map:airports.legend"
      : "map:airports.loading"
  return (
    <p className={styles.airports}>
      <span className={styles.airportDot} aria-hidden="true" />
      {t(key, { count: catalog?.airports.length ?? 0 })}
    </p>
  )
}
