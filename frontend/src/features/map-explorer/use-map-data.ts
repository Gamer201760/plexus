import { useCallback, useMemo } from "react"
import { type Season, useGeoBoundaries, useOverview, useRegions } from "@/entities/region"
import { type MetricKey, metricValue } from "./metric"
import { buildScale } from "./scale"

export function useMapData(metric: MetricKey, season: Season) {
  const geo = useGeoBoundaries()
  const regions = useRegions(season)
  const overview = useOverview()

  const byId = useMemo(() => new Map((regions.data ?? []).map((r) => [r.id, r])), [regions.data])
  const valueAt = useCallback(
    (id: string) => {
      const region = byId.get(id)
      return region ? metricValue(region, metric) : null
    },
    [byId, metric],
  )
  const scale = useMemo(
    () => buildScale((regions.data ?? []).map((region) => metricValue(region, metric))),
    [regions.data, metric],
  )
  const missing = useMemo(
    () => (geo.data?.regions ?? []).some((region) => valueAt(region.id) === null),
    [geo.data, valueAt],
  )
  const failed = geo.isError || regions.isError || overview.isError
  const retry = () => {
    void geo.refetch()
    void regions.refetch()
    void overview.refetch()
  }

  return { geo, regions, overview, byId, valueAt, scale, missing, failed, retry }
}
