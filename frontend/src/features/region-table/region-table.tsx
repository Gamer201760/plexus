import { useState } from "react"
import { useNavigate } from "react-router"
import { type RegionSummary, type Season, useRegions } from "@/entities/region"
import { useFormatters, useTranslation } from "@/shared/i18n"
import {
  DataTable,
  type DataTableColumn,
  ErrorState,
  NoValue,
  Segmented,
  Skeleton,
} from "@/shared/ui"
import styles from "./region-table.module.css"

export function RegionTable() {
  const { t } = useTranslation()
  const f = useFormatters()
  const navigate = useNavigate()
  const [season, setSeason] = useState<Season>("all")
  const regions = useRegions(season)

  const columns: DataTableColumn<RegionSummary>[] = [
    {
      key: "name",
      header: t("region:settlements.name"),
      cell: (r) => r.name,
      sortable: true,
      sortValue: (r) => r.name,
    },
    {
      key: "settlements",
      header: t("region:stats.settlements"),
      cell: (r) => f.integer(r.settlements),
      numeric: true,
      sortable: true,
      sortValue: (r) => r.settlements,
    },
    {
      key: "population",
      header: t("region:stats.population"),
      cell: (r) => f.integer(r.population),
      numeric: true,
      sortable: true,
      sortValue: (r) => r.population,
    },
    {
      key: "links",
      header: t("region:stats.links"),
      cell: (r) => f.integer(r.links_season),
      numeric: true,
      sortable: true,
      sortValue: (r) => r.links_season,
    },
    {
      key: "companies",
      header: t("region:stats.companies"),
      cell: (r) => (r.companies === null ? <NoValue /> : f.integer(r.companies)),
      numeric: true,
      sortable: true,
      sortValue: (r) => r.companies ?? -1,
    },
  ]

  return (
    <div className={styles.table}>
      <Segmented
        label={t("data:season.legend")}
        value={season}
        onChange={setSeason}
        options={(["all", "summer", "winter"] as const).map((key) => ({
          value: key,
          label: t(`data:season.${key}`),
        }))}
      />
      {regions.isError ? (
        <ErrorState title={t("errors:kind.server")} onRetry={() => void regions.refetch()} />
      ) : regions.data ? (
        <DataTable
          caption={t("nav:regions")}
          columns={columns}
          rows={regions.data}
          rowKey={(r) => r.id}
          defaultSort={{ key: "links", direction: "descending" }}
          onRowClick={(r) => void navigate(`/regions/${r.id}`, { viewTransition: true })}
        />
      ) : (
        <Skeleton lines={10} />
      )}
    </div>
  )
}
