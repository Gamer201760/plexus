import type { MapStep, RegionSummary } from "@/entities/region"

export type MetricKey = "links" | "population" | "companies" | "revenuePerCapita"

export const METRICS: readonly MetricKey[] = [
  "links",
  "population",
  "companies",
  "revenuePerCapita",
]

export function metricValue(region: RegionSummary, metric: MetricKey): number | null {
  if (metric === "links") return region.links_season
  if (metric === "population") return region.population
  if (metric === "companies") return region.companies
  if (region.revenue_rub === null || region.population <= 0) return null
  return region.revenue_rub / region.population
}

export function stepScale(regions: readonly RegionSummary[], metric: MetricKey) {
  const positive = regions
    .map((region) => metricValue(region, metric))
    .filter((value): value is number => value !== null && value > 0)
    .sort((a, b) => a - b)
  const thresholds = [1, 2, 3, 4, 5].map(
    (k) => positive[Math.min(positive.length - 1, Math.floor((positive.length * k) / 6))] ?? 0,
  )
  return (value: number | null): MapStep => {
    if (value === null) return 0
    if (value <= 0) return 1
    const index = thresholds.findIndex((threshold) => value < threshold)
    return (index === -1 ? 7 : index + 2) as MapStep
  }
}
