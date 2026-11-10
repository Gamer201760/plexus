import { useQuery } from "@tanstack/react-query"
import { api, unwrap } from "@/shared/api/client"

export function useGraphLocations(query: string) {
  return useQuery({
    queryKey: ["graph-locations", query.trim()],
    enabled: query.trim().length >= 2,
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/road-graph/locations", {
          signal,
          params: { query: { query: query.trim() } },
        }),
      ),
  })
}
