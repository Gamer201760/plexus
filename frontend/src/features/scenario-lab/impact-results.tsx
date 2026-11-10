import type { ScenarioRegionImpact, ScenarioResult } from "@/entities/scenario"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Card, DataTable, type DataTableColumn, NoValue, Stat } from "@/shared/ui"
import styles from "./impact-results.module.css"

export interface ImpactResultsProps {
  readonly result: ScenarioResult
}

type PairRow = ScenarioResult["city_pairs"][number]

const MIN_DELTA = 0.0005

export function ImpactResults({ result }: ImpactResultsProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const impacted = result.regions.filter((region) => Math.abs(region.delta_index) >= MIN_DELTA)
  const delta = result.national_changed_index - result.national_baseline_index
  const regionColumns: DataTableColumn<ScenarioRegionImpact>[] = [
    { key: "name", header: t("scenario:region"), cell: (row) => row.name },
    {
      key: "baseline",
      header: t("scenario:baseline"),
      numeric: true,
      cell: (row) => f.number(row.baseline_index, 2),
    },
    {
      key: "changed",
      header: t("scenario:changed"),
      numeric: true,
      cell: (row) => f.number(row.changed_index, 2),
    },
    {
      key: "delta",
      header: t("scenario:delta"),
      numeric: true,
      cell: (row) => f.number(row.delta_index, 3),
    },
  ]
  const pairColumns: DataTableColumn<PairRow>[] = [
    { key: "from", header: t("scenario:pairFrom"), cell: (row) => row.from_city },
    { key: "to", header: t("scenario:pairTo"), cell: (row) => row.to_city },
    {
      key: "before",
      header: t("scenario:pairBefore"),
      numeric: true,
      cell: (row) => (row.baseline_h === null ? <NoValue /> : f.number(row.baseline_h, 1)),
    },
    {
      key: "after",
      header: t("scenario:pairAfter"),
      numeric: true,
      cell: (row) => f.number(row.changed_h, 1),
    },
  ]
  return (
    <div className={styles.results}>
      <div className={styles.stats}>
        <Stat
          label={t("scenario:national")}
          value={f.number(result.national_changed_index, 3)}
          delta={{
            value: f.number(delta, 3),
            trend: delta > MIN_DELTA ? "up" : "flat",
            tone: delta > MIN_DELTA ? "gain" : "neutral",
          }}
          help={t("scenario:nationalHint")}
        />
        <Stat label={t("scenario:improvedPairs")} value={f.integer(result.improved_city_pairs)} />
      </div>
      {impacted.length === 0 ? (
        <p className={styles.note}>{t("scenario:noImpact")}</p>
      ) : (
        <Card title={t("scenario:regions")} description={t("scenario:regionsHint")}>
          <DataTable
            caption={t("scenario:regions")}
            columns={regionColumns}
            rows={impacted}
            rowKey={(row) => row.region_id}
          />
        </Card>
      )}
      {result.city_pairs.length > 0 && (
        <Card title={t("scenario:pairs")} description={t("scenario:pairsHint")}>
          <DataTable
            caption={t("scenario:pairs")}
            columns={pairColumns}
            rows={result.city_pairs}
            rowKey={(row) => `${row.from_city}:${row.to_city}`}
          />
        </Card>
      )}
      <p className={styles.version}>{t("scenario:version", { version: result.model_version })}</p>
    </div>
  )
}
