import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { useSearchParams } from "react-router"
import { api, unwrap } from "@/shared/api/client"
import type { AnalysisJob, AnalysisMode } from "@/shared/api/road-analysis"

const active = (status: string) => ["queued", "running", "cancelling"].includes(status)

export function useRoadAnalysis(regionId: string | null, mode: AnalysisMode) {
  const cache = useQueryClient()
  const [params, setParams] = useSearchParams()
  const [selectedWay, setSelectedWay] = useState<number | null>(null)
  const recent = useQuery({
    queryKey: ["road-analyses"],
    queryFn: ({ signal }) => unwrap(api.GET("/api/v1/road-analyses", { signal })),
    refetchInterval: 3000,
    retry: false,
  })
  const current =
    params.get("analysis") ??
    recent.data?.find((job) => job.region_id === regionId && job.mode === mode)?.id
  const status = useQuery({
    queryKey: ["road-analysis", current],
    enabled: Boolean(current),
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/road-analyses/{analysis_id}", {
          signal,
          params: { path: { analysis_id: current ?? "" } },
        }),
      ),
    refetchInterval: (query) => (active(query.state.data?.status ?? "queued") ? 1000 : false),
  })
  const update = (job: AnalysisJob) => {
    cache.setQueryData(["road-analysis", job.id], job)
    cache.invalidateQueries({ queryKey: ["road-analyses"] })
    setParams(
      (previous) => {
        previous.set("analysis", job.id)
        previous.set("analysis_mode", job.mode)
        previous.set("region", job.region_id)
        return previous
      },
      { replace: true },
    )
  }
  const start = useMutation({
    mutationFn: (percent: number) =>
      unwrap(
        api.POST("/api/v1/road-analyses", {
          body: { region_id: regionId ?? "", mode, percent },
        }),
      ),
    onSuccess: update,
  })
  const control = useMutation({
    mutationFn: (action: "continue" | "cancel") =>
      action === "continue"
        ? unwrap(
            api.POST("/api/v1/road-analyses/{analysis_id}/continue", {
              params: { path: { analysis_id: current ?? "" } },
            }),
          )
        : unwrap(
            api.POST("/api/v1/road-analyses/{analysis_id}/cancel", {
              params: { path: { analysis_id: current ?? "" } },
            }),
          ),
    onSuccess: update,
  })
  const detailWay = selectedWay ?? status.data?.results.at(-1)?.candidate.way_id ?? null
  const detail = useQuery({
    queryKey: ["road-analysis-detail", current, detailWay],
    enabled: Boolean(current) && detailWay !== null,
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/road-analyses/{analysis_id}/results/{way_id}", {
          signal,
          params: { path: { analysis_id: current ?? "", way_id: detailWay ?? 0 } },
        }),
      ),
  })
  return {
    job: status.data,
    recent: recent.data ?? [],
    start,
    control,
    detail,
    selectedWay,
    selectWay: setSelectedWay,
    busy: active(status.data?.status ?? ""),
    error: recent.isError || status.isError || start.isError || control.isError,
    retry: () => {
      recent.refetch()
      status.refetch()
    },
    selectJob: (id: string) => {
      setSelectedWay(null)
      setParams(
        (p) => {
          p.set("analysis", id)
          const saved = recent.data?.find((item) => item.id === id)
          if (saved) {
            p.set("region", saved.region_id)
            p.set("analysis_mode", saved.mode)
          }
          return p
        },
        { replace: true },
      )
    },
  }
}

export type RoadAnalysisState = ReturnType<typeof useRoadAnalysis>
