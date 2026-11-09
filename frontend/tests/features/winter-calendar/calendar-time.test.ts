import { describe, expect, it } from "vitest"
import type { WinterRoad } from "@/entities/reference"
import {
  calendarKey,
  calendarMonths,
  calendarPosition,
  calendarYears,
  routeRoad,
} from "@/features/winter-calendar/calendar-time"
import calendar from "@/shared/i18n/locales/ru/calendar.json"

const road: WinterRoad = {
  district: "district",
  route: "route",
  road_km: null,
  opening_date: "2024-12-15",
  closure_date: null,
  weight_limit_tonnes: null,
  season_end_year: 2025,
  report_date: "2025-03-01",
  source_file: "report.pdf",
}

describe("winter calendar alignment", () => {
  it("aligns comparison seasons by month and day, not absolute year", () => {
    expect(calendarPosition(2025, "2023-12-15")).toBe(calendarPosition(2025, "2024-12-15"))
    expect(calendarPosition(2025, "2024-03-01")).toBe(calendarPosition(2025, "2025-03-01"))
  })

  it("bounds intervals to the November through May axis", () => {
    expect(calendarPosition(2025, "2024-11-01")).toBe(0)
    expect(calendarPosition(2025, "2025-05-01")).toBe(100)
    expect(calendarPosition(2025, "2025-06-01")).toBe(100)
    expect(calendarMonths(2025).map((month) => month.at)).toEqual(
      ["2024-11-01", "2024-12-01", "2025-01-01", "2025-02-01", "2025-03-01", "2025-04-01"].map(
        (date) => calendarPosition(2025, date),
      ),
    )
  })

  it("keeps routes in different districts distinct across seasons", () => {
    expect(calendarKey(road)).toBe(calendarKey({ ...road, season_end_year: 2024 }))
    expect(calendarKey(road)).not.toBe(calendarKey({ ...road, district: "another" }))
  })

  it("deduplicates known years newest first and excludes aggregate rows", () => {
    expect(
      calendarYears([
        road,
        road,
        { ...road, season_end_year: 2024 },
        { ...road, season_end_year: null },
      ]),
    ).toEqual([2025, 2024])
    const labels = [calendar.totalLabel, calendar.aggregateLabel]
    expect(routeRoad(road, labels)).toBe(true)
    expect(routeRoad({ ...road, route: null }, labels)).toBe(false)
    expect(routeRoad({ ...road, route: calendar.totalLabel.toUpperCase() }, labels)).toBe(false)
  })
})
