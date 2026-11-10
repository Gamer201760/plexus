import type { AnalysisJob } from "./road-analysis"

const record = (value: unknown): value is Record<string, unknown> =>
  value !== null && typeof value === "object"
const finite = (value: unknown): value is number =>
  typeof value === "number" && Number.isFinite(value)

function isResult(row: unknown): boolean {
  return (
    record(row) &&
    ["before", "after", "delta", "affected_population", "isolated_population"].every((key) =>
      finite(row[key]),
    ) &&
    record(row.candidate) &&
    finite(row.candidate.way_id) &&
    typeof row.candidate.name === "string" &&
    finite(row.candidate.length_km)
  )
}

export function isChatAnalysis(value: unknown): value is AnalysisJob {
  if (!record(value)) return false
  return (
    ["id", "region_id", "region", "status", "stage", "fingerprint"].every(
      (key) => typeof value[key] === "string",
    ) &&
    Boolean(value.id) &&
    ["criticality", "improvement"].includes(String(value.mode)) &&
    ["percent", "candidate_count", "batch_target", "completed", "total", "elapsed_seconds"].every(
      (key) => finite(value[key]),
    ) &&
    typeof value.compatible === "boolean" &&
    Array.isArray(value.candidates) &&
    Array.isArray(value.failures) &&
    Array.isArray(value.results) &&
    value.results.every(isResult)
  )
}
