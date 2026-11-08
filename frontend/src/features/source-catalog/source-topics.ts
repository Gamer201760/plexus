import type { IconName } from "@/shared/ui"
export const TOPICS = ["network", "territory", "economy", "seasons"] as const
export type SourceTopic = (typeof TOPICS)[number]
export const TOPIC_ICONS: Record<SourceTopic, IconName> = {
  network: "route",
  territory: "locate",
  economy: "building",
  seasons: "snowflake",
}
const GROUPS: Record<string, SourceTopic> = {
  "atlas-links": "network",
  "transport-operations": "network",
  "northern-delivery": "network",
  "traffic-surveys": "network",
  "atlas-settlements": "territory",
  "region-geometry": "territory",
  "nighttime-lights": "territory",
  rfsd: "economy",
  "fns-revexp": "economy",
  "seasonal-ugra": "seasons",
  "seasonal-closures": "seasons",
}
export function sourceTopic(id: string): SourceTopic {
  return GROUPS[id] ?? "network"
}
export function sourceUsage(id: string) {
  if (id === "atlas-links" || id === "region-geometry") return "atlas"
  if (id === "atlas-settlements") return "settlements"
  if (id === "rfsd" || id === "fns-revexp") return "economy"
  if (id === "seasonal-ugra") return "calendar"
  return "catalog"
}
