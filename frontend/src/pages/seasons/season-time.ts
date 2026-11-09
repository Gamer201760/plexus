import type { WinterRoad } from "@/entities/reference"
import { INTL_LOCALE } from "@/shared/i18n"

const AXIS_START_MONTH = 11
const AXIS_MONTHS = 5
const monthShort = new Intl.DateTimeFormat(INTL_LOCALE, { month: "short" })

export interface SeasonGroup {
  readonly year: number
  readonly roads: readonly WinterRoad[]
}

export interface AxisTick {
  readonly key: string
  readonly label: string
  readonly at: number
}

export interface RoadSpan {
  readonly from: number
  readonly to: number
  readonly open: boolean
}

function axisStart(year: number) {
  return new Date(year - 1, AXIS_START_MONTH, 1).getTime()
}

function axisEnd(year: number) {
  return new Date(year - 1, AXIS_START_MONTH + AXIS_MONTHS, 1).getTime()
}

function position(year: number, iso: string) {
  const [y = 0, m = 1, d = 1] = iso.split("-").map(Number)
  const time = new Date(y, m - 1, d).getTime()
  const start = axisStart(year)
  const ratio = (time - start) / (axisEnd(year) - start)
  return Math.min(1, Math.max(0, ratio))
}

export function seasonTicks(year: number): AxisTick[] {
  const start = axisStart(year)
  const span = axisEnd(year) - start
  return Array.from({ length: AXIS_MONTHS }, (_, index) => {
    const date = new Date(year - 1, AXIS_START_MONTH + index, 1)
    return {
      key: `${date.getFullYear()}-${date.getMonth()}`,
      label: monthShort.format(date),
      at: (date.getTime() - start) / span,
    }
  })
}

export function roadSpan(road: WinterRoad): RoadSpan | null {
  if (road.season_end_year === null || road.opening_date === null) return null
  const end = road.closure_date ?? road.report_date
  if (end === null) return null
  const from = position(road.season_end_year, road.opening_date)
  return { from, to: Math.max(from, position(road.season_end_year, end)), open: !road.closure_date }
}

export function groupBySeason(roads: readonly WinterRoad[]): SeasonGroup[] {
  const years = [...new Set(roads.flatMap((road) => road.season_end_year ?? []))].sort(
    (a, b) => b - a,
  )
  return years.map((year) => ({
    year,
    roads: roads.filter((road) => road.season_end_year === year),
  }))
}

export function seasonYears(year: number) {
  return { from: String(year - 1), to: String(year).slice(-2) }
}

export function routeStops(route: string | null) {
  if (route === null) return []
  return route
    .split(/\s+-\s+/)
    .map((stop) => stop.trim())
    .filter((stop) => stop !== "")
    .map((name, order) => ({ name, key: `${order}-${name}` }))
}

export function roadKey(road: WinterRoad) {
  return `${road.route}-${road.season_end_year}-${road.report_date}`
}
