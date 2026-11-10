import type { RoadGraphState } from "@/entities/road-graph"
import { useTranslation } from "@/shared/i18n"
import { Banner, Button, Card, Stat } from "@/shared/ui"
import { RoadJobSpec } from "./road-job-spec"
import { RoadMoney } from "./road-money"
import styles from "./road-scenario.module.css"
import { SettlementEffects } from "./settlement-effects"

export function RoadResult({ roads }: { readonly roads: RoadGraphState }) {
  const { t } = useTranslation()
  const job = roads.job
  if (!job) return null
  const result = job?.result
  const busy = job?.status === "running" || job?.status === "queued"
  return (
    <Card as="div" className={styles.result} title={job.region}>
      <RoadJobSpec job={job} />
      {busy ? (
        <>
          <p role="status">{t("graph:progress", { count: job.completed, total: job.total })}</p>
          <Button variant="secondary" onClick={() => roads.cancel.mutate()}>
            {t("graph:cancel")}
          </Button>
        </>
      ) : null}
      {job.status === "failed" ? (
        <Banner
          tone="danger"
          title={t(job.error === "baseline_mismatch" ? "graph:mismatch" : "graph:failed")}
        />
      ) : null}
      {job.status === "cancelled" ? <p>{t("graph:cancelled")}</p> : null}
      {result ? (
        <>
          <div className={styles.comparison}>
            <Stat label={t("graph:before")} value={t("graph:number", { value: result.before })} />
            <Stat label={t("graph:after")} value={t("graph:number", { value: result.after })} />
          </div>
          <Stat label={t("graph:delta")} value={t("graph:number", { value: result.delta })} />
          <p className={styles.note}>
            {t("graph:evidence", {
              population: result.population,
              settlements: result.settlements,
              seconds: result.elapsed_seconds,
              edges: result.changed_edges,
            })}
          </p>
          <SettlementEffects result={result} />
          <RoadMoney job={job} />
        </>
      ) : null}
    </Card>
  )
}
