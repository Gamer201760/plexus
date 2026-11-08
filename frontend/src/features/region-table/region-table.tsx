import { useDeferredValue, useState } from "react"
import {
  RegionPreview,
  SeasonControl,
  SeasonPair,
  useRegionCompositions,
  useRegions,
} from "@/entities/region"
import { useSeason } from "@/shared/hooks/use-season"
import { useFormatters, useTranslation } from "@/shared/i18n"
import {
  Card,
  Checkbox,
  DataTable,
  EmptyState,
  ErrorState,
  Select,
  Skeleton,
  TextField,
} from "@/shared/ui"
import { CompositionCell } from "./composition-cell"
import styles from "./region-table.module.css"
import { GROUPS, groupCounts, type TransportGroup } from "./transport-groups"

export function RegionTable() {
  const { t } = useTranslation()
  const f = useFormatters()
  const { season, seasonHref } = useSeason()
  const summer = useRegions("summer")
  const winter = useRegions("winter")
  const regions = season === "summer" ? summer : winter
  const compositions = useRegionCompositions(regions.data ?? [])
  const [groups, setGroups] = useState<readonly TransportGroup[]>(GROUPS)
  const [query, setQuery] = useState("")
  const deferred = useDeferredValue(query)
  const [sort, setSort] = useState("links")
  const [selected, setSelected] = useState("71800000")
  const bySummer = new Map((summer.data ?? []).map((r) => [r.id, r.links_season]))
  const byWinter = new Map((winter.data ?? []).map((r) => [r.id, r.links_season]))
  const rows = (regions.data ?? [])
    .map((r) => {
      const values = groupCounts(compositions.data?.[r.id] ?? [], season, groups)
      return { ...r, values, total: values.reduce((s, v) => s + v.value, 0) }
    })
    .filter(
      (r) =>
        r.total > 0 &&
        r.name.toLocaleLowerCase("ru").includes(deferred.toLocaleLowerCase("ru").trim()),
    )
    .sort((a, b) =>
      sort === "name"
        ? a.name.localeCompare(b.name, "ru")
        : sort === "population"
          ? b.population - a.population
          : sort === "loss"
            ? (bySummer.get(b.id) ?? 0) -
              (byWinter.get(b.id) ?? 0) -
              ((bySummer.get(a.id) ?? 0) - (byWinter.get(a.id) ?? 0))
            : b.total - a.total,
    )
  const active = regions.data?.find((r) => r.id === selected) ?? rows[0]
  const max = Math.max(1, ...rows.map((r) => r.total))
  const failed = regions.isError || summer.isError || winter.isError || compositions.isError
  const retry = () => {
    void summer.refetch()
    void winter.refetch()
    void compositions.refetch()
  }
  if (failed) return <ErrorState title={t("errors:kind.server")} onRetry={retry} />
  if (regions.data?.length === 0) return <EmptyState icon="search" title={t("region:notFound")} />
  if (!regions.data || !summer.data || !winter.data || !compositions.data)
    return <Skeleton lines={12} />
  return (
    <div className={styles.workspace}>
      <Card as="aside" className={styles.filters}>
        <strong>{t("data:season.legend")}</strong>
        <SeasonControl />
        <hr />
        <strong>{t("atlas:transport")}</strong>
        {GROUPS.map((key) => (
          <Checkbox
            key={key}
            label={t(`atlas:groups.${key}`)}
            checked={groups.includes(key)}
            onChange={(on) =>
              setGroups((current) => (on ? [...current, key] : current.filter((g) => g !== key)))
            }
          />
        ))}
      </Card>
      <section className={styles.table}>
        <div className={styles.toolbar}>
          <TextField
            type="search"
            icon="search"
            label={t("region:table.search")}
            hideLabel
            placeholder={t("region:table.search")}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <Select
            label={t("atlas:sort.label")}
            hideLabel
            value={sort}
            onChange={setSort}
            options={["links", "loss", "population", "name"].map((value) => ({
              value,
              label: t(`atlas:sort.${value}` as "atlas:sort.links"),
            }))}
          />
        </div>
        <p className={styles.count} role="status">
          {t("atlas:count", { count: rows.length, total: regions.data.length })}
        </p>
        {rows.length ? (
          <DataTable
            scrollOrientation="horizontal"
            caption={t("nav:regions")}
            rows={rows}
            rowKey={(r) => r.id}
            selectedKey={active?.id}
            onRowPreview={(r) => setSelected(r.id)}
            rowHref={(r) => seasonHref(`/regions/${r.id}`)}
            columns={[
              { key: "name", header: t("atlas:region"), cell: (r) => r.name },
              {
                key: "links",
                header: t("atlas:composition"),
                cell: (r) => <CompositionCell values={r.values} max={max} />,
              },
              {
                key: "seasons",
                header: t("atlas:comparison"),
                cell: (r) => (
                  <SeasonPair
                    summer={bySummer.get(r.id) ?? 0}
                    winter={byWinter.get(r.id) ?? 0}
                    compact
                  />
                ),
              },
              {
                key: "population",
                header: t("region:stats.population"),
                numeric: true,
                cell: (r) => f.compact(r.population),
              },
            ]}
          />
        ) : (
          <EmptyState icon="search" title={t("region:notFound")} />
        )}
      </section>
      {active ? (
        <RegionPreview
          region={active}
          summer={bySummer.get(active.id) ?? 0}
          winter={byWinter.get(active.id) ?? 0}
          rows={regions.data}
        />
      ) : null}
    </div>
  )
}
