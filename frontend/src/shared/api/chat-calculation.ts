import type { components } from "./schema.gen"

export type ChatCalculation = components["schemas"]["CorridorCalculation"]
export type CalculationHandler = (calculation: ChatCalculation, instant?: boolean) => void
export interface CorridorOverlay {
  readonly calculation: ChatCalculation
  readonly focus: number
  readonly instant?: boolean
}

export function isChatCalculation(value: unknown): value is ChatCalculation {
  if (
    typeof value !== "object" ||
    value === null ||
    !("job_ids" in value) ||
    !("corridor" in value)
  )
    return false
  const corridor = value.corridor
  return (
    Array.isArray(value.job_ids) &&
    value.job_ids.length > 0 &&
    value.job_ids.every((id: unknown) => typeof id === "string") &&
    typeof corridor === "object" &&
    corridor !== null &&
    "id" in corridor &&
    typeof corridor.id === "string" &&
    "lines" in corridor &&
    Array.isArray(corridor.lines) &&
    corridor.lines.every(
      (line: unknown) =>
        Array.isArray(line) &&
        line.length >= 2 &&
        line.every(
          (point: unknown) =>
            Array.isArray(point) &&
            point.length === 2 &&
            point.every((v: unknown) => typeof v === "number" && Number.isFinite(v)),
        ),
    )
  )
}
