import type { Mode } from "@/entities/link"
import type { RegionDetail } from "@/entities/region"
export const GROUPS = ["air", "river", "ferry", "winter"] as const
export type TransportGroup = (typeof GROUPS)[number]
export const GROUP_MODES: Record<TransportGroup, readonly Mode[]> = {
  air: ["air"],
  river: ["river"],
  ferry: ["ferry", "pontoon_bridge"],
  winter: ["winter_road", "ice_crossing"],
}
export function groupCounts(
  modes: RegionDetail["links_by_mode"],
  season: "summer" | "winter",
  groups: readonly TransportGroup[],
) {
  return groups.map((key) => ({
    key,
    value: modes
      .filter((m) => GROUP_MODES[key].includes(m.mode))
      .reduce((s, m) => s + m[season], 0),
  }))
}
