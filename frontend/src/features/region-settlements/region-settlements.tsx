import { useDeferredValue, useState } from "react"
import { type Settlement, type SettlementSort, useSettlements } from "@/entities/settlement"
import { useFormatters, useTranslation } from "@/shared/i18n"
import {
  Button,
  Card,
  DataTable,
  type DataTableColumn,
  EmptyState,
  ErrorState,
  NoValue,
  Skeleton,
  type TableSort,
  TextField,
} from "@/shared/ui"
import styles from "./region-settlements.module.css"

const PAGE = 25
const SORTABLE: Record<string, SettlementSort> = {
  name: "name",
  population: "population",
  companies: "companies",
}

export interface RegionSettlementsProps {
  readonly regionId: string
  readonly highlightId: string | null
  readonly onHighlight: (id: string) => void
}

export function RegionSettlements({ regionId, highlightId, onHighlight }: RegionSettlementsProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const [q, setQ] = useState("")
  const query = useDeferredValue(q)
  const [sort, setSort] = useState<TableSort>({ key: "population", direction: "descending" })
  const [offset, setOffset] = useState(0)
  const page = useSettlements({
    regionId,
    q: query,
    sort: SORTABLE[sort.key] ?? "population",
    order: sort.direction === "ascending" ? "asc" : "desc",
    limit: PAGE,
    offset,
  })

  const columns: DataTableColumn<Settlement>[] = [
    { key: "name", header: t("region:settlements.name"), cell: (s) => s.name, sortable: true },
    {
      key: "population",
      header: t("region:settlements.population"),
      cell: (s) => (s.population === null ? <NoValue /> : f.integer(s.population)),
      numeric: true,
      sortable: true,
    },
    {
      key: "companies",
      header: t("region:settlements.companies"),
      cell: (s) => (s.companies === null ? <NoValue /> : f.integer(s.companies)),
      numeric: true,
      sortable: true,
    },
  ]

  const total = page.data?.total ?? 0
  return (
    <Card as="section" title={t("region:settlements.title")} className={styles.card}>
      <TextField
        label={t("region:settlements.search")}
        hideLabel
        icon="search"
        placeholder={t("region:settlements.search")}
        value={q}
        onChange={(event) => {
          setQ(event.target.value)
          setOffset(0)
        }}
      />
      {page.isError ? (
        <ErrorState title={t("errors:kind.server")} onRetry={() => void page.refetch()} />
      ) : !page.data ? (
        <Skeleton lines={8} />
      ) : page.data.items.length === 0 ? (
        <EmptyState icon="search" title={t("region:settlements.empty")} />
      ) : (
        <div className={page.isPlaceholderData ? styles.stale : undefined}>
          <DataTable
            caption={t("region:settlements.title")}
            columns={columns}
            rows={page.data.items}
            rowKey={(s) => s.id}
            sort={sort}
            onSortChange={(next) => {
              setSort(next)
              setOffset(0)
            }}
            selectedKey={highlightId}
            onRowClick={(s) => onHighlight(s.id)}
          />
        </div>
      )}
      {total > PAGE ? (
        <div className={styles.pager}>
          <span className={styles.pageText}>
            {t("region:settlements.page", {
              from: offset + 1,
              to: Math.min(offset + PAGE, total),
              total,
            })}
          </span>
          <Button
            variant="secondary"
            size="compact"
            icon="arrow-left"
            disabled={offset === 0}
            onClick={() => setOffset(Math.max(0, offset - PAGE))}
          >
            {t("region:settlements.prev")}
          </Button>
          <Button
            variant="secondary"
            size="compact"
            icon="arrow-right"
            disabled={offset + PAGE >= total}
            onClick={() => setOffset(offset + PAGE)}
          >
            {t("region:settlements.next")}
          </Button>
        </div>
      ) : null}
    </Card>
  )
}
