import { useDeferredValue, useState } from "react"
import { type RegionSummary, type Season, useRegions } from "@/entities/region"
import { useFormatters, useTranslation } from "@/shared/i18n"
import {
  DataTable,
  EmptyState,
  ErrorState,
  Segmented,
  Skeleton,
  type TableSort,
  TextField,
} from "@/shared/ui"
import { DEFAULT_METRIC, isMetric, regionColumns } from "./region-columns"
import styles from "./region-table.module.css"

const SEASONS = ["all", "summer", "winter"] as const
const DIAERESIS = String.fromCodePoint(0x0308)

function fold(text: string) {
  return text.toLocaleLowerCase("ru").normalize("NFD").replaceAll(DIAERESIS, "").trim()
}

function matches(rows: readonly RegionSummary[], query: string) {
  const needle = fold(query)
  if (needle === "") return rows
  return rows.filter((row) => fold(row.name).includes(needle))
}

export function RegionTable() {
  const { t } = useTranslation()
  const f = useFormatters()
  const [season, setSeason] = useState<Season>("all")
  const [query, setQuery] = useState("")
  const [sort, setSort] = useState<TableSort>({ key: DEFAULT_METRIC, direction: "descending" })
  const regions = useRegions(season)
  const deferred = useDeferredValue(query)
  const all = regions.data ?? []
  const rows = matches(all, deferred)
  const columns = regionColumns({
    rows: all,
    barKey: isMetric(sort.key) ? sort.key : DEFAULT_METRIC,
    f,
    header: (key) => (key === "name" ? t("region:settlements.name") : t(`region:stats.${key}`)),
  })

  const table =
    rows.length === 0 ? (
      <EmptyState icon="search" title={t("region:notFound")} />
    ) : (
      <DataTable
        caption={t("nav:regions")}
        columns={columns}
        rows={rows}
        rowKey={(r) => r.id}
        sort={sort}
        onSortChange={setSort}
        rowHref={(r) => `/regions/${r.id}`}
        className={styles.scroller}
      />
    )

  return (
    <div className={styles.table}>
      <div className={styles.toolbar}>
        <TextField
          type="search"
          icon="search"
          label={t("region:table.search")}
          placeholder={t("region:table.search")}
          hideLabel
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          className={styles.search}
        />
        <Segmented
          label={t("data:season.legend")}
          value={season}
          onChange={setSeason}
          options={SEASONS.map((key) => ({ value: key, label: t(`data:season.${key}`) }))}
        />
      </div>
      {regions.isError ? (
        <ErrorState title={t("errors:kind.server")} onRetry={() => void regions.refetch()} />
      ) : regions.data ? (
        table
      ) : (
        <Skeleton lines={10} className={styles.rowsBone} />
      )}
    </div>
  )
}
