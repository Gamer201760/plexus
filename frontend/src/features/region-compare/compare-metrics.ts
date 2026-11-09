import type { RegionSummary } from "@/entities/region"
import type { Formatters } from "@/shared/i18n"

export type CompareMetricLabel =
  | "data:metric.hansen"
  | "data:metric.links"
  | "data:metric.population"
  | "region:stats.settlements"
  | "data:metric.companies"
  | "data:network.coverageColumn"

export type CompareMetricHint =
  | "data:metricHint.hansen"
  | "data:metricHint.links"
  | "data:metricHint.population"
  | "data:metricHint.settlements"
  | "data:metricHint.companies"
  | "data:network.coverageHint"

export interface CompareMetric {
  readonly key: string
  readonly label: CompareMetricLabel
  readonly hint: CompareMetricHint
  readonly value: (region: RegionSummary) => number | null
  readonly format: (value: number, f: Formatters) => string
}

export const COMPARE_METRICS: readonly CompareMetric[] = [
  {
    key: "hansen",
    label: "data:metric.hansen",
    hint: "data:metricHint.hansen",
    value: (region) => region.hansen,
    format: (value, f) => f.number(value, 2),
  },
  {
    key: "coverage",
    label: "data:network.coverageColumn",
    hint: "data:network.coverageHint",
    value: (region) => region.index_population_coverage ?? null,
    format: (value, f) => f.percent(value, 1),
  },
  {
    key: "links",
    label: "data:metric.links",
    hint: "data:metricHint.links",
    value: (region) => region.links_season,
    format: (value, f) => f.integer(value),
  },
  {
    key: "population",
    label: "data:metric.population",
    hint: "data:metricHint.population",
    value: (region) => region.population,
    format: (value, f) => f.compact(value),
  },
  {
    key: "settlements",
    label: "region:stats.settlements",
    hint: "data:metricHint.settlements",
    value: (region) => region.settlements,
    format: (value, f) => f.integer(value),
  },
  {
    key: "companies",
    label: "data:metric.companies",
    hint: "data:metricHint.companies",
    value: (region) => region.companies,
    format: (value, f) => f.compact(value),
  },
]
