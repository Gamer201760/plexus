import type { Pilot, PilotResult } from "@/entities/pilot"

function save(content: string, name: string, type: string) {
  const url = URL.createObjectURL(new Blob([content], { type }))
  const anchor = document.createElement("a")
  anchor.href = url
  anchor.download = name
  anchor.click()
  URL.revokeObjectURL(url)
}

export function exportParameters(pilot: Pilot, result: PilotResult) {
  save(
    JSON.stringify({ pilot, evaluation: result }, null, 2),
    "plexus-experiment.json",
    "application/json",
  )
}

export function exportComparison(pilot: Pilot, result: PilotResult, headers: readonly string[]) {
  const records = result.pairs.map((pair) => {
    const trip = pilot.pairs.find((item) => item.id === pair.pair_id)
    const name = (id: string | undefined) =>
      pilot.points.find((point) => point.id === id)?.name ?? id ?? ""
    return [
      name(trip?.from_id),
      name(trip?.to_id),
      result.season,
      pair.baseline.total_h,
      pair.changed.total_h,
      pair.changed.travel_h,
      pair.changed.waiting_h,
      pair.delta_h,
      pair.changed.status,
      result.model_version,
      result.artifact_version,
      JSON.stringify(result.changes),
      JSON.stringify([...result.assumptions, ...pair.changed.assumptions]),
      JSON.stringify(pair.changed.edge_ids),
    ]
  })
  const csv = [headers, ...records]
    .map((row) => row.map((cell) => `"${String(cell ?? "").replaceAll('"', '""')}"`).join(";"))
    .join("\r\n")
  save(`\ufeff${csv}`, "plexus-comparison.csv", "text/csv;charset=utf-8")
}
