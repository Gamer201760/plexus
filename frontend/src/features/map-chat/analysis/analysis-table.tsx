import type { AnalysisJob, VerifiedRoad } from "@/shared/api/road-analysis"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { DataTable, type DataTableColumn } from "@/shared/ui"
import styles from "./chat-analysis.module.css"

export function AnalysisTable({ job }: { readonly job: AnalysisJob }) {
  const { t } = useTranslation()
  const f = useFormatters()
  const rows = [...job.results].sort(
    (a, b) =>
      (job.mode === "improvement" ? b.delta - a.delta : a.delta - b.delta) ||
      a.candidate.way_id - b.candidate.way_id,
  )
  const ranks = new Map(rows.map((row, index) => [row.candidate.way_id, index + 1]))
  const columns: DataTableColumn<VerifiedRoad>[] = [
    {
      key: "road",
      header: t("chat:analysis.road"),
      cell: (row) => (
        <span className={styles.road}>
          <strong>
            {t("chat:analysis.rankedRoad", {
              rank: ranks.get(row.candidate.way_id) ?? 0,
              name: row.candidate.name || t("analysis:way", { id: row.candidate.way_id }),
            })}
          </strong>
          <span className={styles.note}>{t("analysis:way", { id: row.candidate.way_id })}</span>
        </span>
      ),
    },
    {
      key: "delta",
      header: t("chat:analysis.delta"),
      numeric: true,
      cell: (row) => f.number(row.delta, 6),
    },
    {
      key: "population",
      header: t("chat:analysis.population"),
      numeric: true,
      cell: (row) => f.integer(row.affected_population),
    },
  ]
  if (job.mode === "criticality")
    columns.push({
      key: "isolated",
      header: t("chat:analysis.isolated"),
      numeric: true,
      cell: (row) => f.integer(row.isolated_population),
    })
  return (
    <DataTable
      className={styles.table}
      caption={t("chat:analysis.ranking")}
      columns={columns}
      rows={rows}
      rowKey={(row) => String(row.candidate.way_id)}
    />
  )
}
