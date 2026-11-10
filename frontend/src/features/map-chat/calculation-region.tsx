import type { UseQueryResult } from "@tanstack/react-query"
import type { RoadJob } from "@/shared/api/road-graph"
import { useTranslation } from "@/shared/i18n"
import { Swap } from "@/shared/motion"
import { Banner, Button, Meter } from "@/shared/ui"
import styles from "./chat-calculation.module.css"

export function CalculationRegion({
  query,
  name,
}: {
  readonly query: UseQueryResult<RoadJob>
  readonly name: string | undefined
}) {
  const { t } = useTranslation()
  const job = query.data
  const state = query.isError ? "error" : (job?.status ?? "loading")
  return (
    <div className={styles.region}>
      <strong>{job?.region ?? name}</strong>
      <Swap swapKey={state}>
        {query.isError ? (
          <Banner
            tone="danger"
            title={t("graph:requestError")}
            action={<Button onClick={() => void query.refetch()}>{t("chat:retry")}</Button>}
          />
        ) : (
          <CalculationState job={job} />
        )}
      </Swap>
    </div>
  )
}

function CalculationState({ job }: { readonly job: RoadJob | undefined }) {
  const { t } = useTranslation()
  if (job?.result)
    return (
      <>
        <dl className={styles.numbers}>
          <div>
            <dt>{t("graph:before")}</dt>
            <dd>{t("graph:number", { value: job.result.before })}</dd>
          </div>
          <div>
            <dt>{t("graph:after")}</dt>
            <dd>{t("graph:number", { value: job.result.after })}</dd>
          </div>
        </dl>
        <p>
          <strong>
            {t("graph:delta")}: {t("graph:number", { value: job.result.delta })}
          </strong>
        </p>
      </>
    )
  if (job?.status === "failed")
    return (
      <Banner
        tone="danger"
        title={t(job.error === "baseline_mismatch" ? "graph:mismatch" : "graph:failed")}
      />
    )
  if (job?.status === "cancelled") return <p>{t("graph:cancelled")}</p>
  return (
    <>
      <p role="status">
        {t(job?.status === "queued" ? "chat:calculation.queued" : "chat:calculation.running")}
      </p>
      <Meter
        value={job?.completed ?? 0}
        max={job?.total ?? 360}
        label={t("chat:calculation.progress")}
      />
      <p className={styles.note}>
        {t("chat:calculation.count", { count: job?.completed ?? 0, total: job?.total ?? 360 })}
      </p>
    </>
  )
}
