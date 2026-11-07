import { useState } from "react"
import { useWinterRoads, type WinterRoad } from "@/entities/reference"
import { useDocumentTitle, useFormatters, useTranslation } from "@/shared/i18n"
import {
  DataTable,
  type DataTableColumn,
  ErrorState,
  NoValue,
  PageHeader,
  Select,
  Skeleton,
  StatusBadge,
} from "@/shared/ui"
import styles from "./seasons-page.module.css"

const ALL = "all-districts"

export function SeasonsPage() {
  const { t } = useTranslation()
  const f = useFormatters()
  useDocumentTitle(t("seasons:title"))
  const roads = useWinterRoads()
  const [district, setDistrict] = useState(ALL)
  const districts = [
    ...new Set((roads.data ?? []).flatMap((road) => (road.district ? [road.district] : []))),
  ]
  const rows = (roads.data ?? []).filter((road) => district === ALL || road.district === district)

  const columns: DataTableColumn<WinterRoad>[] = [
    {
      key: "route",
      header: t("seasons:route"),
      cell: (road) => road.route ?? <NoValue />,
      sortable: true,
      sortValue: (road) => road.route ?? "",
    },
    {
      key: "district",
      header: t("seasons:district"),
      cell: (road) => road.district ?? <NoValue />,
    },
    {
      key: "length",
      header: t("seasons:length"),
      cell: (road) =>
        road.road_km === null ? <NoValue /> : `${f.number(road.road_km)} ${t("data:unit.km")}`,
      numeric: true,
      sortable: true,
      sortValue: (road) => road.road_km ?? -1,
    },
    {
      key: "opened",
      header: t("seasons:opened"),
      cell: (road) => (road.opening_date ? f.date(road.opening_date) : <NoValue />),
    },
    {
      key: "closed",
      header: t("seasons:closed"),
      cell: (road) =>
        road.closure_date ? (
          f.date(road.closure_date)
        ) : (
          <StatusBadge tone="info" label={t("seasons:stillOpen")} />
        ),
    },
    {
      key: "weight",
      header: t("seasons:weight"),
      cell: (road) =>
        road.weight_limit_tonnes === null ? (
          <NoValue />
        ) : (
          `${f.number(road.weight_limit_tonnes)} ${t("data:unit.tonnes")}`
        ),
      numeric: true,
    },
    {
      key: "season",
      header: t("seasons:season"),
      cell: (road) => (road.season_end_year === null ? <NoValue /> : String(road.season_end_year)),
      numeric: true,
    },
  ]

  return (
    <div className={styles.page}>
      <PageHeader
        title={t("seasons:title")}
        description={t("seasons:lead")}
        actions={
          <Select
            label={t("seasons:district")}
            hideLabel
            value={district}
            onChange={setDistrict}
            options={[
              { value: ALL, label: t("seasons:allDistricts") },
              ...districts.map((name) => ({ value: name, label: name })),
            ]}
          />
        }
      />
      {roads.isError ? (
        <ErrorState title={t("errors:kind.server")} onRetry={() => void roads.refetch()} />
      ) : roads.data ? (
        <DataTable
          caption={t("seasons:title")}
          columns={columns}
          rows={rows}
          rowKey={(road) => `${road.route}-${road.season_end_year}-${road.report_date}`}
        />
      ) : (
        <Skeleton lines={10} />
      )}
    </div>
  )
}
