import { useQuery, useQueryClient } from "@tanstack/react-query"
import { api, unwrap } from "@/shared/api"
import { type RegionDetail, type RegionSummary, regionKeys } from "./region.queries"

export function useRegionCompositions(regions: readonly RegionSummary[]) {
  const client = useQueryClient()
  const ids = regions
    .filter((r) => r.links > 0)
    .map((r) => r.id)
    .sort()
  return useQuery({
    queryKey: ["region-compositions", ids],
    enabled: regions.length > 0,
    staleTime: Infinity,
    queryFn: async ({ signal }) => {
      const result: Record<string, RegionDetail["links_by_mode"]> = {}
      for (let i = 0; i < ids.length; i += 6) {
        const batch = await Promise.all(
          ids.slice(i, i + 6).map((id) =>
            client.fetchQuery({
              queryKey: regionKeys.detail(id, "all"),
              staleTime: Infinity,
              queryFn: () =>
                unwrap(
                  api.GET("/api/v1/regions/{region_id}", {
                    params: { path: { region_id: id }, query: { season: "all" } },
                    signal,
                  }),
                ),
            }),
          ),
        )
        for (const region of batch) result[region.id] = region.links_by_mode
      }
      return result
    },
  })
}
