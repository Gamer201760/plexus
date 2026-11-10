import type { components } from "./schema.gen"

export type AnalysisJob = components["schemas"]["AnalysisResponse"]
export type AnalysisDetail = components["schemas"]["AnalysisDetail"]
export type AnalysisMode = "criticality" | "improvement"
export type VerifiedRoad = components["schemas"]["VerifiedRoad"]
export interface AnalysisOverlay {
  readonly detail: AnalysisDetail
  readonly instant?: boolean
  readonly focus: number
}
