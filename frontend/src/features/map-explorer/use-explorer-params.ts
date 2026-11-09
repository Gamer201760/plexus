import { useCallback } from "react"
import { useSearchParams } from "react-router"
import type { Season } from "@/entities/region"
import { DEFAULT_METRIC, DEFAULT_SEASON, isMetricKey, isSeason, type MetricKey } from "./metric"

type ParamKey = "region" | "metric" | "season"

type Patch = Partial<Record<ParamKey, string | null>>

function applyPatch(current: URLSearchParams, patch: Patch): URLSearchParams {
  const next = new URLSearchParams(current)
  for (const [key, value] of Object.entries(patch)) {
    if (value === null || value === undefined) next.delete(key)
    else next.set(key, value)
  }
  return next
}

export function useExplorerParams() {
  const [params, setParams] = useSearchParams()
  const rawMetric = params.get("metric")
  const rawSeason = params.get("season")
  const metric: MetricKey = isMetricKey(rawMetric) ? rawMetric : DEFAULT_METRIC
  const requestedSeason: Season = isSeason(rawSeason) ? rawSeason : DEFAULT_SEASON
  const season = metric === "hansen" && requestedSeason === "all" ? "summer" : requestedSeason
  const selectedId = params.get("region")

  const update = useCallback(
    (patch: Patch) => setParams((current) => applyPatch(current, patch), { replace: true }),
    [setParams],
  )

  const setMetric = useCallback(
    (next: MetricKey) =>
      update({
        metric: next === DEFAULT_METRIC ? null : next,
        ...(next === "hansen" && season === "all" ? { season: "summer" } : {}),
      }),
    [update, season],
  )
  const setSeason = useCallback(
    (next: Season) => update({ season: next === DEFAULT_SEASON ? null : next }),
    [update],
  )
  const select = useCallback((id: string | null) => update({ region: id }), [update])
  const searchFor = useCallback(
    (id: string) => `?${applyPatch(params, { region: id }).toString()}`,
    [params],
  )

  return { metric, season, selectedId, setMetric, setSeason, select, searchFor }
}
