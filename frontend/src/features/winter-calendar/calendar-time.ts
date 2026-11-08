import type { WinterRoad } from "@/entities/reference"
import { INTL_LOCALE } from "@/shared/i18n"
export function calendarPosition(year: number, date: string) {
  const [, month = 1, day = 1] = date.split("-").map(Number)
  const start = Date.UTC(year - 1, 10, 1)
  const end = Date.UTC(year, 4, 1)
  return Math.max(
    0,
    Math.min(
      100,
      ((Date.UTC(month >= 11 ? year - 1 : year, month - 1, day) - start) / (end - start)) * 100,
    ),
  )
}
export function calendarMonths(year: number) {
  const format = new Intl.DateTimeFormat(INTL_LOCALE, { month: "long", timeZone: "UTC" })
  return Array.from({ length: 6 }, (_, i) => {
    const date = new Date(Date.UTC(year - 1, 10 + i, 1))
    return {
      key: i,
      label: format.format(date),
      at: calendarPosition(year, date.toISOString().slice(0, 10)),
    }
  })
}
export function calendarKey(road: WinterRoad) {
  return `${road.district ?? ""}:${road.route ?? ""}`
}
export function calendarYears(roads: readonly WinterRoad[]) {
  return [
    ...new Set(roads.flatMap((r) => (r.season_end_year === null ? [] : [r.season_end_year]))),
  ].sort((a, b) => b - a)
}
export function routeRoad(road: WinterRoad, aggregateLabels: readonly string[]) {
  return (
    road.route !== null &&
    !aggregateLabels.some((label) => road.route?.toLocaleLowerCase("ru").startsWith(label))
  )
}
