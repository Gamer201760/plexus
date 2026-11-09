import type { RegionSummary } from "@/entities/region"

type Row = RegionSummary & { readonly total: number }

export function compareRegionRows(
  left: Row,
  right: Row,
  sort: string,
  summer: ReadonlyMap<string, number>,
  winter: ReadonlyMap<string, number>,
): number {
  if (sort === "name") return left.name.localeCompare(right.name, "ru")
  if (sort === "hansen") return (right.hansen ?? -1) - (left.hansen ?? -1)
  if (sort === "population") return right.population - left.population
  if (sort === "loss") {
    const loss = (row: Row) => (summer.get(row.id) ?? 0) - (winter.get(row.id) ?? 0)
    return loss(right) - loss(left)
  }
  return right.total - left.total
}
