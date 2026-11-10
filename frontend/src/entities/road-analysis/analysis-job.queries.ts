import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useRef } from "react"
import { api, unwrap } from "@/shared/api/client"
import type { AnalysisJob } from "@/shared/api/road-analysis"

export function useAnalysisJob(initial: AnalysisJob) {
  const cache = useQueryClient()
  const received = useRef(initial)
  useEffect(() => {
    if (received.current === initial) return
    received.current = initial
    cache.setQueryData(["road-analysis", initial.id], initial)
  }, [cache, initial])
  return useQuery({
    queryKey: ["road-analysis", initial.id],
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/road-analyses/{analysis_id}", {
          signal,
          params: { path: { analysis_id: initial.id } },
        }),
      ),
    initialData: initial,
    refetchInterval: (query) =>
      ["queued", "running", "cancelling"].includes(query.state.data?.status ?? "queued")
        ? 1000
        : false,
  })
}
