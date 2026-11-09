import { useMutation, useQuery } from "@tanstack/react-query"
import { api, type components, unwrap } from "@/shared/api"

export type Pilot = components["schemas"]["PilotResponse"]
export type PilotEdge = components["schemas"]["EdgeResponse"]
export type PilotResult = components["schemas"]["EvaluationResponse"]
export type PilotRequest = components["schemas"]["EvaluationRequest"]
export type PilotChange = components["schemas"]["EdgeChangeRequest"]
export type PilotPairResult = components["schemas"]["PairComparisonResponse"]

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
