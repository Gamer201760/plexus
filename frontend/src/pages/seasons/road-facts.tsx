import type { ReactNode } from "react"
import type { WinterRoad } from "@/entities/reference"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { NoValue, type SortValue, StatusBadge } from "@/shared/ui"
import { seasonYears } from "./season-time"

export interface RoadFact {
  readonly key: string
  readonly label: string
  readonly numeric: boolean
  readonly value: (road: WinterRoad) => ReactNode
  readonly sortValue?: ((road: WinterRoad) => SortValue) | undefined
}

export function useRoadFacts(): RoadFact[] {
  const { t } = useTranslation()
  const f = useFormatters()
  const amount = (value: number | null, unit: string) =>
    value === null ? <NoValue /> : `${f.number(value)} ${unit}`
  return [
    {
      key: "district",
      label: t("seasons:district"),
      numeric: false,
      value: (road) => road.district ?? <NoValue />,
    },
    {
      key: "length",
      label: t("seasons:length"),
      numeric: true,
      value: (road) => amount(road.road_km, t("data:unit.km")),
      sortValue: (road) => road.road_km ?? -1,
    },
    {
      key: "opened",
      label: t("seasons:opened"),
      numeric: false,
      value: (road) => (road.opening_date ? f.date(road.opening_date) : <NoValue />),
      sortValue: (road) => road.opening_date,
    },
    {
      key: "closed",
      label: t("seasons:closed"),
      numeric: false,
      value: (road) =>
        road.closure_date ? (
          f.date(road.closure_date)
        ) : (
          <StatusBadge tone="info" label={t("seasons:stillOpen")} />
        ),
    },
    {
      key: "weight",
      label: t("seasons:weight"),
      numeric: true,
      value: (road) => amount(road.weight_limit_tonnes, t("data:unit.tonnes")),
    },
    {
      key: "season",
      label: t("seasons:season"),
      numeric: false,
      value: (road) =>
        road.season_end_year === null ? (
          <NoValue />
        ) : (
          t("seasons:winterOf", seasonYears(road.season_end_year))
        ),
      sortValue: (road) => road.season_end_year,
    },
  ]
}
