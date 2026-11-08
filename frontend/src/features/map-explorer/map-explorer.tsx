import { useCallback, useMemo, useState } from "react"
import { useSearchParams } from "react-router"
import {
  type MapControls,
  type MapStep,
  RegionPreview,
  RussiaMap,
  SeasonControl,
  useGeoRegions,
  useRegions,
} from "@/entities/region"
import { useSeason } from "@/shared/hooks/use-season"
import { useTranslation } from "@/shared/i18n"
import { ErrorState, Select, Skeleton } from "@/shared/ui"
import styles from "./atlas-map.module.css"
import { MapZoom } from "./map-zoom"

export function MapExplorer() {
  const { t } = useTranslation()
  const { season } = useSeason()
  const geo = useGeoRegions()
  const summer = useRegions("summer")
  const winter = useRegions("winter")
  const rows = (season === "summer" ? summer.data : winter.data) ?? []
  const [metric, setMetric] = useState("delta")
  const [params, setParams] = useSearchParams()
  const selected = params.get("region") ?? "71800000"
  const setSelected = useCallback(
    (id: string) => {
      setParams(
        (current) => {
          const next = new URLSearchParams(current)
          next.set("region", id)
          return next
        },
        { replace: true, preventScrollReset: true },
      )
    },
    [setParams],
  )
  const [hovered, setHovered] = useState<string | null>(null)
  const sums = useMemo(
    () => new Map((summer.data ?? []).map((r) => [r.id, r.links_season])),
    [summer.data],
  )
  const winters = useMemo(
    () => new Map((winter.data ?? []).map((r) => [r.id, r.links_season])),
    [winter.data],
  )
  const values = useMemo(
    () =>
      new Map(
        (season === "summer" ? summer.data : winter.data)?.map((r) => [r.id, r.links_season]) ?? [],
      ),
    [season, summer.data, winter.data],
  )
  const stepOf = useCallback(
    (id: string): MapStep => {
      const a = sums.get(id) ?? 0
      const b = winters.get(id) ?? 0
      if (!a && !b) return 0
      if (metric === "delta") return deltaStep(a, b)
      const max = Math.max(1, ...values.values())
      const count = values.get(id) ?? 0
      return count ? (Math.min(7, 1 + Math.floor((count / max) * 6)) as MapStep) : 0
    },
    [metric, sums, winters, values],
  )
  const onHover = useCallback((id: string | null) => setHovered(id), [])
  const controls = useCallback(
    (value: MapControls) => <MapZoom controls={value} onReset={() => setSelected("71800000")} />,
    [setSelected],
  )
  const active = rows.find((r) => r.id === (hovered ?? selected)) ?? rows[0]
  if (geo.isError || summer.isError || winter.isError)
    return (
      <ErrorState
        title={t("errors:kind.server")}
        onRetry={() => {
          void geo.refetch()
          void summer.refetch()
          void winter.refetch()
        }}
      />
    )
  if (!geo.data || !summer.data || !winter.data) return <Skeleton lines={12} />
  return (
    <div className={styles.workspace}>
      <section className={styles.panel}>
        <div className={styles.toolbar}>
          <SeasonControl />
          <Select
            label={t("data:metric.label")}
            hideLabel
            value={metric}
            onChange={setMetric}
            options={[
              { value: "delta", label: t("atlas:delta") },
              { value: "count", label: t("atlas:countMetric") },
            ]}
          />
        </div>
        <div className={styles.map}>
          <RussiaMap
            viewBox={geo.data.view_box}
            regions={geo.data.regions}
            palette={metric === "delta" ? "delta" : "count"}
            focusSelected={false}
            stepOf={stepOf}
            selectedId={hovered ?? selected}
            label={t("map:label")}
            onSelect={setSelected}
            onHover={onHover}
            controls={controls}
          />
        </div>
        <div className={styles.legend}>
          {(metric === "delta"
            ? (["loss", "gain", "equal", "none"] as const)
            : (["none"] as const)
          ).map((key) => (
            <span key={key}>
              <i data-tone={key} />
              {t(`atlas:${key}`)}
            </span>
          ))}
          {metric === "count" ? <span>{t("atlas:countMetric")}</span> : null}
        </div>
      </section>
      {active ? (
        <RegionPreview
          region={active}
          summer={sums.get(active.id) ?? 0}
          winter={winters.get(active.id) ?? 0}
          rows={rows}
          withMap={false}
        />
      ) : null}
    </div>
  )
}

function deltaStep(summer: number, winter: number): MapStep {
  if (winter < summer) return 1
  if (winter > summer) return 3
  return 2
}
