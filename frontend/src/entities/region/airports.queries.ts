import { useQuery } from "@tanstack/react-query"
import { api, unwrap } from "@/shared/api/client"

export function useAirports() {
  return useQuery({
    queryKey: ["airports"],
    queryFn: ({ signal }) => unwrap(api.GET("/api/v1/airports", { signal })),
    staleTime: Infinity,
    retry: false,
  })
}
