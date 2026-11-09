import type { RegionSummary } from "@/entities/region"
import type { Formatters } from "@/shared/i18n"
import { type DataTableColumn, NoValue } from "@/shared/ui"
import { MetricCell } from "./metric-cell"

export type MetricKey = "settlements" | "population" | "links" | "companies"

interface MetricSpec {
  readonly key: MetricKey
  readonly value: (row: RegionSummary) => number | null
}

export const METRICS: readonly MetricSpec[] = [
  { key: "settlements", value: (r) => r.settlements },
  { key: "population", value: (r) => r.population },
  { key: "links", value: (r) => r.links_season },
  { key: "companies", value: (r) => r.companies },
]

export const DEFAULT_METRIC: MetricKey = "links"

export function isMetric(key: string): key is MetricKey {
  return METRICS.some((metric) => metric.key === key)
}

export interface ColumnOptions {
  readonly rows: readonly RegionSummary[]
  readonly barKey: MetricKey
  readonly f: Formatters
  readonly header: (key: "name" | MetricKey) => string
}

export function regionColumns({
  rows,
  barKey,
  f,
  header,
}: ColumnOptions): DataTableColumn<RegionSummary>[] {
  const metrics = METRICS.map((metric): DataTableColumn<RegionSummary> => {
    const max = Math.max(0, ...rows.map((row) => metric.value(row) ?? 0))
    return {
      key: metric.key,
      header: header(metric.key),
      numeric: true,
      sortable: true,
      sortValue: (row) => metric.value(row) ?? -1,
      cell: (row) => {
        const value = metric.value(row)
        return (
          <MetricCell value={value} max={max} bar={metric.key === barKey}>
            {value === null ? <NoValue /> : f.integer(value)}
          </MetricCell>
        )
      },
    }
  })
  return [
    {
      key: "name",
      header: header("name"),
      cell: (row) => row.name,
      sortable: true,
      sortValue: (row) => row.name,
    },
    ...metrics,
  ]
}
