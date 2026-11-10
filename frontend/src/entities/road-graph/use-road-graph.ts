import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useCallback, useEffect, useRef, useState } from "react"
import type { ChatCalculation, CorridorOverlay } from "@/shared/api/chat-calculation"
import { api, unwrap } from "@/shared/api/client"
import type { AnalysisOverlay } from "@/shared/api/road-analysis"
import type {
  ConnectionInput,
  RoadBounds,
  RoadJob,
  RoadSegment,
  RoadView,
} from "@/shared/api/road-graph"

export function useRoadGraph() {
  const [corridorOverlay, setCorridorOverlay] = useState<CorridorOverlay | null>(null)
  const showCalculation = useCallback((calculation: ChatCalculation, instant = false) => {
    setCorridorOverlay({ calculation, focus: performance.now(), instant })
    setSelectedJobId(calculation.job_ids[0] ?? null)
  }, [])
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)
  const [analysisOverlay, setAnalysisOverlay] = useState<AnalysisOverlay | null>(null)
  const [bounds, setBounds] = useState<RoadBounds | null>(null)
  const [selected, setSelected] = useState<readonly RoadSegment[]>([])
  const [enabled, setEnabled] = useState(true)
  const cache = useQueryClient()
  const view = useQuery<RoadView>({
    queryKey: ["road-graph", bounds],
    placeholderData: keepPreviousData,
    enabled: enabled && bounds !== null,
    retry: false,
    queryFn: ({ signal }) => {
      const [west, south, east, north, zoom] = bounds ?? [0, 0, 1, 1, 8]
      return unwrap<RoadView>(
        api.GET("/api/v1/road-graph", {
          signal,
          params: { query: { west, south, east, north, zoom } },
        }),
      )
    },
  })
  const lastView = useRef<RoadView | undefined>(undefined)
  useEffect(() => {
    if (view.data) lastView.current = view.data
  }, [view.data])
  const recent = useQuery({
    queryKey: ["road-scenarios"],
    queryFn: ({ signal }) => unwrap(api.GET("/api/v1/road-scenarios", { signal })),
    refetchInterval: 3000,
    retry: false,
  })
  const current = recent.data?.find((job) => job.id === selectedJobId) ?? recent.data?.[0] ?? null
  const status = useQuery({
    queryKey: ["road-scenario", current?.id],
    enabled: current !== null,
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/road-scenarios/{job_id}", {
          signal,
          params: { path: { job_id: current?.id ?? "" } },
        }),
      ),
    refetchInterval: (query) =>
      ["queued", "running"].includes(query.state.data?.status ?? "queued") ? 1500 : false,
  })
  const submit = useMutation({
    mutationFn: (body: {
      region_id: string
      scenario: "road" | "summer" | "winter"
      changes: { way_id: number; speed_factor: number }[]
    }) => unwrap(api.POST("/api/v1/road-scenarios", { body })),
    onSuccess: (job) => {
      setSelectedJobId(job.id)
      cache.setQueryData<RoadJob[]>(["road-scenarios"], (current) => [
        job,
        ...(current ?? []).filter((item) => item.id !== job.id),
      ])
    },
  })
  const addConnection = useMutation({
    mutationFn: (body: ConnectionInput) => unwrap(api.POST("/api/v1/road-connections", { body })),
    onSuccess: (job) => {
      setSelectedJobId(job.id)
      cache.setQueryData<RoadJob[]>(["road-scenarios"], (current) => [
        job,
        ...(current ?? []).filter((item) => item.id !== job.id),
      ])
    },
  })
  const cancel = useMutation({
    mutationFn: () =>
      unwrap(
        api.DELETE("/api/v1/road-scenarios/{job_id}", {
          params: { path: { job_id: current?.id ?? "" } },
        }),
      ),
    onSuccess: () => status.refetch(),
  })
  const onRoad = useCallback((road: RoadSegment) => {
    setSelected((current) =>
      current.some((r) => r.way_id === road.way_id)
        ? current.filter((r) => r.way_id !== road.way_id)
        : current.length < 50
          ? [...current, road]
          : current,
    )
  }, [])
  return {
    corridorOverlay,
    showCalculation,
    jobs: recent.data ?? [],
    selectJob: setSelectedJobId,
    analysisOverlay,
    setAnalysisOverlay,
    view,
    layerView: enabled ? (view.data ?? lastView.current) : undefined,
    selected,
    enabled,
    setEnabled,
    onBounds: setBounds,
    onRoad,
    clear: () => setSelected([]),
    submit,
    addConnection,
    cancel,
    job: status.data ?? current,
    statusError: status.isError,
  }
}

export type RoadGraphState = ReturnType<typeof useRoadGraph>
