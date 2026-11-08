import { useMemo, useState } from "react"
import { useSearchParams } from "react-router"
import {
  type Box,
  RussiaMap,
  type Season,
  useGeoRegions,
  useOverview,
  useRegion,
  useRegions,
} from "@/entities/region"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Button, ErrorState, Skeleton, Tooltip } from "@/shared/ui"
import { formatMetric } from "./format-metric"
import { HoverCard } from "./hover-card"
import styles from "./map-explorer.module.css"
import { MapLegend } from "./map-legend"
import { MapPanel } from "./map-panel"
import { MapToolbar } from "./map-toolbar"
import { type MetricKey, metricValue, stepScale } from "./metric"

interface Hover {
  readonly id: string
  readonly x: number
  readonly y: number
}

export function MapExplorer() {
  const { t } = useTranslation()
  const f = useFormatters()
  const [params, setParams] = useSearchParams()
  const [season, setSeason] = useState<Season>("all")
  const [metric, setMetric] = useState<MetricKey>("links")
  const [hover, setHover] = useState<Hover | null>(null)
  const selectedId = params.get("region")
  const geo = useGeoRegions()
  const regions = useRegions(season)
  const overview = useOverview()
  const selected = useRegion(selectedId ?? "", season)

  const byId = useMemo(() => new Map((regions.data ?? []).map((r) => [r.id, r])), [regions.data])
  const step = useMemo(() => stepScale(regions.data ?? [], metric), [regions.data, metric])
  const focusBox = useMemo<Box | null>(() => {
    const bbox = selectedId ? selected.data?.bbox : null
    if (!bbox) return null
    const [x = 0, y = 0, width = 1, height = 1] = bbox
    return { x, y, width, height }
  }, [selectedId, selected.data])

  const select = (id: string | null) => {
    setParams(id ? { region: id } : {}, { replace: true })
  }

  if (geo.isError || regions.isError || overview.isError) {
    return (
      <ErrorState
        title={t("errors:kind.server")}
        onRetry={() => {
          void geo.refetch()
          void regions.refetch()
          void overview.refetch()
        }}
      />
    )
  }

  const hovered = hover ? byId.get(hover.id) : undefined
  const hoveredValue = hovered ? metricValue(hovered, metric) : null

  return (
    <div className={styles.explorer}>
      <div className={styles.stage}>
        {geo.data && regions.data ? (
          <RussiaMap
            viewBox={geo.data.view_box}
            regions={geo.data.regions}
            stepOf={(id) => {
              const region = byId.get(id)
              return step(region ? metricValue(region, metric) : null)
            }}
            selectedId={selectedId}
            focusBox={focusBox}
            label={t("map:label")}
            onSelect={select}
            onHover={(id, x, y) => setHover(id ? { id, x, y } : null)}
            controls={(controls) => (
              <div className={styles.zoom}>
                <Tooltip content={t("map:zoomIn")} side="bottom" describe={false}>
                  <Button
                    variant="secondary"
                    size="compact"
                    icon="plus"
                    onClick={controls.zoomIn}
                    aria-label={t("map:zoomIn")}
                  >
                    {null}
                  </Button>
                </Tooltip>
                <Tooltip content={t("map:zoomOut")} side="bottom" describe={false}>
                  <Button
                    variant="secondary"
                    size="compact"
                    icon="minus"
                    onClick={controls.zoomOut}
                    aria-label={t("map:zoomOut")}
                  >
                    {null}
                  </Button>
                </Tooltip>
                <Tooltip content={t("map:reset")} side="bottom" describe={false}>
                  <Button
                    variant="secondary"
                    size="compact"
                    icon="locate"
                    onClick={() => select(null)}
                    aria-label={t("map:reset")}
                  >
                    {null}
                  </Button>
                </Tooltip>
              </div>
            )}
          />
        ) : (
          <Skeleton shape="block" className={styles.mapSkeleton} />
        )}
        <MapToolbar metric={metric} season={season} onMetric={setMetric} onSeason={setSeason} />
        <MapLegend metric={metric} />
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
