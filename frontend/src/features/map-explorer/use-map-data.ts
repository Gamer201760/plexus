import { useCallback, useMemo } from "react"
import {
  type Box,
  type Season,
  useGeoRegions,
  useOverview,
  useRegion,
  useRegions,
} from "@/entities/region"
import { type MetricKey, metricValue } from "./metric"
import { buildScale } from "./scale"

export function useMapData(metric: MetricKey, season: Season, selectedId: string | null) {
  const geo = useGeoRegions()
  const regions = useRegions(season)
  const overview = useOverview()
  const selected = useRegion(selectedId ?? "", season)

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
  const focusBox = useMemo<Box | null>(() => {
    const bbox = selectedId ? selected.data?.bbox : null
    if (!bbox) return null
    const [x = 0, y = 0, width = 1, height = 1] = bbox
    return { x, y, width, height }
  }, [selectedId, selected.data])

  const failed = geo.isError || regions.isError || overview.isError
  const retry = () => {
    void geo.refetch()
    void regions.refetch()
    void overview.refetch()
  }

  return { geo, regions, overview, byId, valueAt, scale, missing, focusBox, failed, retry }
}
