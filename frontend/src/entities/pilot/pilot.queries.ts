import { useMutation, useQuery } from "@tanstack/react-query"
import { api, type components, unwrap } from "@/shared/api"

export type Pilot = components["schemas"]["PilotResponse"]
export type PilotSummary = components["schemas"]["PilotSummaryResponse"]
export type PilotEdge = components["schemas"]["EdgeResponse"]
export type PilotResult = components["schemas"]["EvaluationResponse"]
export type PilotRequest = components["schemas"]["EvaluationRequest"]
export type PilotChange = components["schemas"]["EdgeChangeRequest"]
export type PilotPairResult = components["schemas"]["PairComparisonResponse"]

const LEGACY_PILOT_IDS: Readonly<Record<string, string>> = { "93000000": "tuva" }

export function pilotIdForRegion(
  regionId: string,
  pilots: readonly PilotSummary[] | undefined,
): string | null {
  if (pilots === undefined) return null
  if (pilots.some((pilot) => pilot.id === regionId)) return regionId
  const legacy = LEGACY_PILOT_IDS[regionId]
  if (legacy !== undefined && pilots.some((pilot) => pilot.id === legacy)) return legacy
  return null
}

export function usePilots() {
  return useQuery({
    queryKey: ["pilots"],
    queryFn: ({ signal }) => unwrap(api.GET("/api/v1/pilots", { signal })),
    staleTime: Number.POSITIVE_INFINITY,
  })
}

export function usePilot(id: string) {
  return useQuery({
    queryKey: ["pilot", id],
    queryFn: ({ signal }) =>
      unwrap(api.GET("/api/v1/pilots/{pilot_id}", { params: { path: { pilot_id: id } }, signal })),
  })
}

export function useEvaluatePilot(id: string) {
  return useMutation({
    mutationFn: (body: PilotRequest) =>
      unwrap(
        api.POST("/api/v1/pilots/{pilot_id}/evaluate", {
          params: { path: { pilot_id: id } },
          body,
        }),
      ),
  })
}
