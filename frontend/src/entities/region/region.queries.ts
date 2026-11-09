import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { api, type components, unwrap } from "@/shared/api"
import { type NetworkMode, useNetworkMode } from "@/shared/hooks/use-network-mode"

export type Season = components["schemas"]["Season"]
export type RegionSummary = components["schemas"]["RegionSummaryResponse"]
export type RegionDetail = components["schemas"]["RegionDetailResponse"]
export type GeoRegions = components["schemas"]["GeoRegionsResponse"]
export type Overview = components["schemas"]["OverviewResponse"]
export type TransportModeKey = components["schemas"]["Mode"]

export const regionKeys = {
  geo: ["geo", "regions"] as const,
  boundaries: ["geo", "boundaries"] as const,
  overview: ["overview"] as const,
  list: (season: Season, mode: NetworkMode = "road") => ["regions", season, mode] as const,
  detail: (id: string, season: Season, mode: NetworkMode = "road") =>
    ["region", id, season, mode] as const,
}

export function useGeoRegions() {
  return useQuery({
    queryKey: regionKeys.geo,
    queryFn: ({ signal }) => unwrap(api.GET("/api/v1/geo/regions", { signal })),
    staleTime: Number.POSITIVE_INFINITY,
  })
}

export function useGeoBoundaries() {
  return useQuery({
    queryKey: regionKeys.boundaries,
    queryFn: ({ signal }) => unwrap(api.GET("/api/v1/geo/boundaries", { signal })),
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
  const { networkMode } = useNetworkMode()
  return useQuery({
    queryKey: regionKeys.list(season, networkMode),
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/regions", {
          params: { query: { season, network_mode: networkMode } },
          signal,
        }),
      ),
    placeholderData: keepPreviousData,
  })
}

export function useRegion(id: string, season: Season) {
  const { networkMode } = useNetworkMode()
  return useQuery({
    queryKey: regionKeys.detail(id, season, networkMode),
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/regions/{region_id}", {
          params: { path: { region_id: id }, query: { season, network_mode: networkMode } },
          signal,
        }),
      ),
    enabled: id.length > 0,
    placeholderData: keepPreviousData,
  })
}
