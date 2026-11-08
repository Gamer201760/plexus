import { useState } from "react"
import { RussiaMap } from "@/entities/region"
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

interface Hover {
  readonly id: string
  readonly x: number
  readonly y: number
}

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
  const [hover, setHover] = useState<Hover | null>(null)
  const { geo, regions, overview, byId, valueAt, scale, missing, focusBox, failed, retry } =
    useMapData(metric, season, selectedId)

  if (failed) return <ErrorState title={t("errors:kind.server")} onRetry={retry} />

  const hovered = hover ? byId.get(hover.id) : undefined
  const hoveredValue = hovered ? metricValue(hovered, metric) : null
  const ready = geo.data !== undefined && regions.data !== undefined

  return (
    <div className={styles.explorer}>
      <div className={styles.stage}>
        {geo.data && regions.data ? (
          <RussiaMap
            viewBox={geo.data.view_box}
            regions={geo.data.regions}
            stepOf={(id) => scale.stepOf(valueAt(id))}
            selectedId={selectedId}
            focusBox={focusBox}
            label={t("map:label")}
            onSelect={select}
            onHover={(id, x, y) => setHover(id ? { id, x, y } : null)}
            controls={(controls) => <MapZoom controls={controls} onReset={() => select(null)} />}
          />
        ) : (
          <MapLoading />
        )}
        <div className={styles.overlay}>
          <MapToolbar metric={metric} season={season} onMetric={setMetric} onSeason={setSeason} />
          {ready ? <MapLegend metric={metric} scale={scale} missing={missing} /> : null}
        </div>
        {hover && hovered ? (
          <HoverCard
            x={hover.x}
            y={hover.y}
            title={hovered.name}
            label={t(`data:metric.${metric}`)}
            value={hoveredValue === null ? null : formatMetric(hoveredValue, metric, f)}
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
          onClear={() => select(null)}
        />
      ) : (
        <div className={styles.panelLoading}>
          <Skeleton lines={8} />
        </div>
      )}
    </div>
  )
}
