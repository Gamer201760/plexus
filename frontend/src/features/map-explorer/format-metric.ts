import type { Formatters } from "@/shared/i18n"
import type { MetricKey } from "./metric"

export function formatMetric(value: number, metric: MetricKey, f: Formatters): string {
  if (metric === "hansen") return f.number(value, 2)
  if (metric === "links") return f.integer(value)
  if (metric === "revenuePerCapita") return f.money(value, "RUB", 0)
  return f.compact(value)
}

export function formatThreshold(value: number, metric: MetricKey, f: Formatters): string {
  if (metric === "hansen") return f.number(value, 2)
  return metric === "links" ? f.integer(value) : f.compact(value)
}
