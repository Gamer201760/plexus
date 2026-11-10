import type { CorridorOverlay } from "./chat-calculation"
import type { AnalysisOverlay } from "./road-analysis"
import type { components } from "./schema.gen"

export type RoadSegment = components["schemas"]["RoadSegment"]
export type RoadView = components["schemas"]["RoadView"]
export type GraphLocation = components["schemas"]["GraphLocation"]
export type ConnectionInput = components["schemas"]["RoadAdditionInput"]
export type RoadJob = components["schemas"]["RoadJob"]
export type RoadBounds = readonly [number, number, number, number, number]

export interface RoadLayerProps {
  readonly corridor?: CorridorOverlay | null | undefined
  readonly analysis?: AnalysisOverlay | null | undefined
  readonly addition?: RoadJob["addition"] | undefined
  readonly view: RoadView | undefined
  readonly selected: readonly RoadSegment[]
  readonly onBounds: (bounds: RoadBounds) => void
  readonly onRoad: (road: RoadSegment) => void
}
