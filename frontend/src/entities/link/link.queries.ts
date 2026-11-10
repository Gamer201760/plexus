import { useQuery } from "@tanstack/react-query"
import { api, type components, unwrap } from "@/shared/api"

export type Link = components["schemas"]["LinkResponse"]
export type Mode = components["schemas"]["Mode"]
type Season = components["schemas"]["Season"]

export const linkKeys = {
  region: (id: string | null, season: Season) => ["links", id, season] as const,
}

export function useRegionLinks(id: string | null, season: Season) {
  return useQuery({
    queryKey: linkKeys.region(id, season),
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/regions/{region_id}/links", {
          params: { path: { region_id: id ?? "" }, query: { season, include_unknown: true } },
          signal,
        }),
      ),
    enabled: id !== null && id.length > 0,
  })
}
