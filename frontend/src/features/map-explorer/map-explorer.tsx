import { useCallback } from "react"
import { type MapControls, RussiaMap } from "@/entities/region"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { ErrorState, Skeleton } from "@/shared/ui"
import { Isolines } from "@/shared/ui/brand"
import { formatMetric } from "./format-metric"
import { HoverCard } from "./hover-card"
import styles from "./map-explorer.module.css"
import { MapLegend } from "./map-legend"
import { MapPanel } from "./map-panel"
import { MapToolbar } from "./map-toolbar"
import { MapZoom } from "./map-zoom"
import { metricValue } from "./metric"
import { useExplorerParams } from "./use-explorer-params"
import { useMapData } from "./use-map-data"
import { useMapHover } from "./use-map-hover"

function MapLoading() {
  const { t } = useTranslation()
  return (
    <div className={styles.mapLoading} role="status">
      <Isolines rings={3} motion="pulse" className={styles.loadingRings} />
      <span className="visually-hidden">{t("common:state.loading")}</span>
    </div>
  )
}

export function MapExplorer() {
  const { t } = useTranslation()
  const f = useFormatters()
  const { metric, season, selectedId, setMetric, setSeason, select, searchFor } =
    useExplorerParams()
  const { hoveredId, cardRef, point, onHover } = useMapHover()
  const { geo, regions, overview, byId, valueAt, scale, missing, failed, retry } = useMapData(
    metric,
    season,
  )

  const stepOf = useCallback((id: string) => scale.stepOf(valueAt(id)), [scale, valueAt])
  const clear = useCallback(() => select(null), [select])
  const controls = useCallback(
    (value: MapControls) => <MapZoom controls={value} onReset={clear} />,
    [clear],
  )

  if (failed) return <ErrorState title={t("errors:kind.server")} onRetry={retry} />

  const hovered = hoveredId ? byId.get(hoveredId) : undefined
  const hoveredIndex = hovered ? hovered.hansen : null
  const hoveredValue = hovered ? metricValue(hovered, metric) : null
  const indexRow = {
    key: "hansen",
    label: t("data:metric.hansen"),
    value: hoveredIndex === null ? null : formatMetric(hoveredIndex, "hansen", f),
  }
  const metricRow = {
    key: metric,
    label: t(`data:metric.${metric}`),
    value: hoveredValue === null ? null : formatMetric(hoveredValue, metric, f),
  }
  const hoverRows = metric === "hansen" ? [indexRow] : [indexRow, metricRow]
  const ready = geo.data !== undefined && regions.data !== undefined

  return (
    <div className={styles.explorer}>
      <div className={styles.stage}>
        {geo.data && regions.data ? (
          <RussiaMap
            viewBox={geo.data.view_box}
            regions={geo.data.regions}
            stepOf={stepOf}
            selectedId={selectedId}
            label={t("map:label")}
            onSelect={select}
            onHover={onHover}
            controls={controls}
          />
        ) : (
          <MapLoading />
        )}
        <div className={styles.overlay}>
          <MapToolbar metric={metric} season={season} onMetric={setMetric} onSeason={setSeason} />
          {ready ? <MapLegend metric={metric} scale={scale} missing={missing} /> : null}
        </div>
        {hovered ? (
          <HoverCard
            cardRef={cardRef}
            point={point}
            title={hovered.name}
            rows={hoverRows}
            none={t("map:legend.none")}
          />
        ) : null}
      </div>
      {overview.data && regions.data ? (
        <MapPanel
          overview={overview.data}
          regions={regions.data}
          metric={metric}
          season={season}
          selectedId={selectedId}
          searchFor={searchFor}
          onClear={clear}
        />
      ) : (
        <div className={styles.panelLoading}>
          <Skeleton lines={8} />
        </div>
      )}
    </div>
  )
}
