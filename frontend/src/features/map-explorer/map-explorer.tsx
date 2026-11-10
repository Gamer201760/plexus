import { type ReactNode, useCallback, useState } from "react"
import { useLocation } from "react-router"
import { type MapControls, OsmMap } from "@/entities/region"
import { type RoadGraphState, useRoadGraph } from "@/entities/road-graph"
import type { ChatMapCommand, MapCommandHandler } from "@/shared/api/chat-map"
import type { ChatContext } from "@/shared/api/chat-stream"
import { useNetworkMode } from "@/shared/hooks/use-network-mode"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { ErrorState, Skeleton } from "@/shared/ui"
import { Isolines } from "@/shared/ui/brand"
import { formatMetric } from "./format-metric"
import { HoverCard } from "./hover-card"
import styles from "./map-explorer.module.css"
import { AirportLegend, MapLegend, TransitLegend } from "./map-legend"
import { MapPanel } from "./map-panel"
import { MapToolbar } from "./map-toolbar"
import { MapZoom } from "./map-zoom"
import { metricValue } from "./metric"
import { RoadLegend } from "./road-legend"
import { useExplorerParams } from "./use-explorer-params"
import { useMapData, useSelectedTransit } from "./use-map-data"
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

export interface MapExplorerProps {
  readonly renderPanel?: (
    summary: ReactNode,
    context: ChatContext,
    onMapCommand: MapCommandHandler,
    roads: RoadGraphState,
    onChatChange: () => void,
  ) => ReactNode
}

export function MapExplorer({ renderPanel }: MapExplorerProps) {
  const roads = useRoadGraph()
  const { networkMode } = useNetworkMode()
  const fullscreen = useLocation().pathname === "/"
  const { t } = useTranslation()
  const f = useFormatters()
  const { metric, season, selectedId, setMetric, setSeason, select, searchFor } =
    useExplorerParams()
  const { links, airports, transit, modelCount, showModels, setShowModels } = useSelectedTransit(
    selectedId,
    season,
  )
  const { hoveredId, cardRef, point, onHover } = useMapHover()
  const { geo, regions, overview, byId, valueAt, scale, missing, failed, retry } = useMapData(
    metric,
    season,
  )

  const [mapCommand, setMapCommand] = useState<ChatMapCommand | null>(null)
  const selectRegion = useCallback(
    (id: string | null) => {
      setMapCommand(null)
      select(id)
    },
    [select],
  )
  const onMapCommand = useCallback<MapCommandHandler>(
    (command) => {
      if (command.action === "focus") {
        if (!command.region_ids.every((id) => geo.data?.regions.some((region) => region.id === id)))
          return
        select(command.region_ids.length === 1 ? (command.region_ids[0] ?? null) : null)
      }
      if (command.action === "reset") select(null)
      setMapCommand({ ...command })
    },
    [geo.data, select],
  )

  const stepOf = useCallback((id: string) => scale.stepOf(valueAt(id)), [scale, valueAt])
  const clear = useCallback(() => selectRegion(null), [selectRegion])
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

  const panel =
    overview.data && regions.data ? (
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
    )

  return (
    <div className={styles.explorer} data-fullscreen={fullscreen}>
      <div className={styles.stage}>
        {geo.data && regions.data ? (
          <OsmMap
            transit={transit.data}
            airports={airports.data}
            roads={{
              view: roads.layerView,
              onRendering: roads.setRendering,
              addition: roads.addition,
              analysis: roads.analysisOverlay,
              corridor: roads.corridorOverlay,
              selected: roads.selected,
              onBounds: roads.onBounds,
              onRoad: roads.onRoad,
            }}
            regions={geo.data.regions}
            stepOf={stepOf}
            selectedId={selectedId}
            label={t("map:label")}
            attribution={t("map:attribution")}
            onSelect={selectRegion}
            command={mapCommand}
            onHover={onHover}
            controls={controls}
          />
        ) : (
          <MapLoading />
        )}
        <div className={styles.overlay}>
          <MapToolbar metric={metric} season={season} onMetric={setMetric} onSeason={setSeason} />
          {ready ? (
            <MapLegend metric={metric} scale={scale} missing={missing}>
              <RoadLegend roads={roads} />
              <AirportLegend catalog={airports.data} failed={airports.isError} />
              <TransitLegend
                selectedId={selectedId}
                loading={links.isPending}
                failed={links.isError}
                missing={transit.missing}
                modeled={modelCount > 0}
                modelCount={modelCount}
                showModels={showModels}
                onModelsChange={setShowModels}
                empty={transit.data.features.length === 0}
                onRetry={() => void links.refetch()}
              />
            </MapLegend>
          ) : null}
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
      {renderPanel
        ? renderPanel(
            panel,
            {
              region_id: selectedId,
              season,
              network_mode: networkMode,
              metric,
            },
            onMapCommand,
            roads,
            () => {
              setMapCommand(null)
              roads.clearOverlays()
            },
          )
        : panel}
    </div>
  )
}
