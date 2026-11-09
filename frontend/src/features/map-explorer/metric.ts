import type { RegionSummary, Season } from "@/entities/region"

export type MetricKey = "hansen" | "links" | "population" | "companies" | "revenuePerCapita"

export const METRICS: readonly MetricKey[] = [
  "hansen",
  "links",
  "population",
  "companies",
  "revenuePerCapita",
]

export const SEASONS: readonly Season[] = ["all", "summer", "winter"]

export const DEFAULT_METRIC: MetricKey = "hansen"

export const DEFAULT_SEASON: Season = "all"

export function isMetricKey(value: string | null): value is MetricKey {
  return METRICS.some((metric) => metric === value)
}

export function isSeason(value: string | null): value is Season {
  return SEASONS.some((season) => season === value)
}

export function dependsOnSeason(metric: MetricKey): boolean {
  return metric === "links" || metric === "hansen"
}

export function metricValue(region: RegionSummary, metric: MetricKey): number | null {
  if (metric === "hansen") return region.hansen
  if (metric === "links") return region.links_season
  if (metric === "population") return region.population
  if (metric === "companies") return region.companies
  if (region.revenue_rub === null || region.population <= 0) return null
  return region.revenue_rub / region.population
}
