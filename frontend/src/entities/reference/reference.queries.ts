import { useQuery } from "@tanstack/react-query"
import { api, type components, unwrap } from "@/shared/api"

export type Source = components["schemas"]["SourceResponse"]
export type WinterRoad = components["schemas"]["WinterRoadResponse"]
export type IndexStatus = components["schemas"]["IndexStatusResponse"]

export const referenceKeys = {
  sources: ["sources"] as const,
  winterRoads: ["seasons", "winter-roads"] as const,
  index: ["index"] as const,
}

export function useSources() {
  return useQuery({
    queryKey: referenceKeys.sources,
    queryFn: ({ signal }) => unwrap(api.GET("/api/v1/sources", { signal })),
  })
}

export function useWinterRoads() {
  return useQuery({
    queryKey: referenceKeys.winterRoads,
    queryFn: ({ signal }) => unwrap(api.GET("/api/v1/seasons/winter-roads", { signal })),
  })
}

export function useIndexStatus() {
  return useQuery({
    queryKey: referenceKeys.index,
    queryFn: ({ signal }) => unwrap(api.GET("/api/v1/index", { signal })),
  })
}
