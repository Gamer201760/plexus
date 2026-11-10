import { useMemo, useState } from "react"
import type { AnalysisJob } from "@/shared/api/road-analysis"
import { useTranslation } from "@/shared/i18n"
import { Button, Segmented } from "@/shared/ui"
import styles from "./road-analysis.module.css"

interface AnalysisRankingProps {
  readonly job: AnalysisJob
  readonly selectedWay: number | null
  readonly onSelect: (id: number) => void
}

export function AnalysisRanking({ job, selectedWay, onSelect }: AnalysisRankingProps) {
  const { t } = useTranslation()
  const [ranking, setRanking] = useState<"access" | "isolation">("access")
  const [order, setOrder] = useState<number[]>([])
  const sorted = useMemo(
    () =>
      [...job.results].sort((a, b) => {
        const population =
          ranking === "isolation" ? b.isolated_population - a.isolated_population : 0
        const effect = job.mode === "criticality" ? a.delta - b.delta : b.delta - a.delta
        return population || effect || a.candidate.way_id - b.candidate.way_id
      }),
    [job.results, job.mode, ranking],
  )
  const byId = new Map(sorted.map((r) => [r.candidate.way_id, r]))
  const ids = [
    ...order.filter((id) => byId.has(id)),
    ...sorted.map((r) => r.candidate.way_id).filter((id) => !order.includes(id)),
  ]
  const changed = ids.some((id, i) => id !== sorted[i]?.candidate.way_id)
  return (
    <div className={styles.ranking}>
      <p className={styles.note}>
        {t("analysis:bestChecked", { count: job.results.length, total: job.candidate_count })}
      </p>
      {job.mode === "criticality" ? (
        <Segmented
          label={t("analysis:ranking")}
          value={ranking}
          onChange={(value) => {
            setRanking(value)
            setOrder([])
          }}
          options={[
            { value: "access", label: t("analysis:accessRanking") },
            { value: "isolation", label: t("analysis:isolationRanking") },
          ]}
        />
      ) : null}
      {changed ? (
        <Button
          icon="retry"
          variant="secondary"
          onClick={() => setOrder(sorted.map((r) => r.candidate.way_id))}
        >
          {t("analysis:reorder")}
        </Button>
      ) : null}
      {!job.results.length ? <p>{t("analysis:noVerified")}</p> : null}
      {ranking === "isolation" &&
      job.results.length > 0 &&
      !job.results.some((r) => r.isolated_population > 0) ? (
        <p>{t("analysis:noIsolation")}</p>
      ) : null}
      <ol
        className={styles.list}
        onPointerEnter={() => {
          if (!order.length) setOrder(ids)
        }}
        onFocusCapture={() => {
          if (!order.length) setOrder(ids)
        }}
      >
        {ids.map((id) => {
          const row = byId.get(id)
          if (!row) return null
          return (
            <li key={id} className={styles.row}>
              <Button
                variant={selectedWay === id ? "primary" : "secondary"}
                icon="map"
                wrap
                onClick={() => {
                  setOrder(ids)
                  onSelect(id)
                }}
              >
                {row.candidate.name}
              </Button>
              <span>{t("analysis:roadLength", { value: row.candidate.length_km })}</span>
              <strong>
                {ranking === "isolation"
                  ? t("analysis:people", { count: row.isolated_population })
                  : t("analysis:delta", { value: row.delta })}
              </strong>
              <span>{t("analysis:affected", { count: row.affected_population })}</span>
              {Math.abs(row.delta) < 1e-6 ? <span>{t("analysis:zeroEffect")}</span> : null}
            </li>
          )
        })}
      </ol>
    </div>
  )
}
