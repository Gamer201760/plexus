import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { api, type components, unwrap } from "@/shared/api"

export type Season = components["schemas"]["Season"]
export type RegionSummary = components["schemas"]["RegionSummaryResponse"]
export type RegionDetail = components["schemas"]["RegionDetailResponse"]
export type GeoRegions = components["schemas"]["GeoRegionsResponse"]
export type Overview = components["schemas"]["OverviewResponse"]

export const regionKeys = {
  geo: ["geo", "regions"] as const,
  overview: ["overview"] as const,
  list: (season: Season) => ["regions", season] as const,
  detail: (id: string, season: Season) => ["region", id, season] as const,
}

export function useGeoRegions() {
  return useQuery({
    queryKey: regionKeys.geo,
    queryFn: ({ signal }) => unwrap(api.GET("/api/v1/geo/regions", { signal })),
    staleTime: Number.POSITIVE_INFINITY,
  })
}

export function useOverview() {
  return useQuery({
    queryKey: regionKeys.overview,
    queryFn: ({ signal }) => unwrap(api.GET("/api/v1/overview", { signal })),
  })
}

export function useRegions(season: Season) {
  return useQuery({
    queryKey: regionKeys.list(season),
    queryFn: ({ signal }) =>
      unwrap(api.GET("/api/v1/regions", { params: { query: { season } }, signal })),
    placeholderData: keepPreviousData,
  })
}

export function useRegion(id: string, season: Season) {
  return useQuery({
    queryKey: regionKeys.detail(id, season),
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/regions/{region_id}", {
          params: { path: { region_id: id }, query: { season } },
          signal,
        }),
      ),
    enabled: id.length > 0,
    placeholderData: keepPreviousData,
  })
}
