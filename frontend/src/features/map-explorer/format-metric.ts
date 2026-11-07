import type { Formatters } from "@/shared/i18n"
import type { MetricKey } from "./metric"

export function formatMetric(value: number, metric: MetricKey, f: Formatters): string {
  if (metric === "links") return f.integer(value)
  if (metric === "revenuePerCapita") return f.money(Math.round(value), "RUB")
  return f.compact(value)
}
