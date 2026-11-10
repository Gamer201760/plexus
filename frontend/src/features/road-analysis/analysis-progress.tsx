import type { AnalysisJob } from "@/shared/api/road-analysis"
import { useTranslation } from "@/shared/i18n"
import { Swap } from "@/shared/motion"
import { Button, Icon, Meter } from "@/shared/ui"
import styles from "./road-analysis.module.css"

interface AnalysisProgressProps {
  readonly job: AnalysisJob
  readonly busy: boolean
  readonly pending: boolean
  readonly control: (action: "continue" | "cancel") => void
}

export function AnalysisProgress({ job, busy, pending, control }: AnalysisProgressProps) {
  const { t } = useTranslation()
  const checked = job.results.length + job.failures.length
  const labels: Record<string, string> = {
    queued: t("analysis:queued"),
    cancelled: t("analysis:cancelled"),
    interrupted: t("analysis:interrupted"),
    failed: t("analysis:failed"),
    cancelling: t("analysis:cancelling"),
    preparing: t("analysis:preparing"),
    geography: t("analysis:geography"),
    screening: t("analysis:screening"),
    topology: t("analysis:topology"),
    verifying: t("analysis:verifying"),
    complete: t("analysis:complete"),
    batch_complete: t("analysis:batchComplete"),
  }
  return (
    <div className={styles.progress} aria-busy={busy}>
      <Swap swapKey={`${job.status}-${job.stage}`}>
        <p role="status" className={styles.stage}>
          <Icon name={busy ? "neutral" : "check"} />
          {labels[job.status] ?? labels[job.stage]}
        </p>
      </Swap>
      <p>
        {t("analysis:checked", {
          count: checked,
          total: Math.min(job.batch_target, job.candidate_count || job.batch_target),
        })}
      </p>
      {busy && job.total > 1 ? (
        <>
          <Meter value={job.completed} max={job.total} label={t("analysis:stageProgress")} />
          <span>{t("analysis:stageCount", { count: job.completed, total: job.total })}</span>
        </>
      ) : null}
      {job.current_way_id ? <p>{t("analysis:current", { id: job.current_way_id })}</p> : null}
      {busy ? (
        <Button
          icon="stop"
          variant="secondary"
          disabled={pending || job.status === "cancelling"}
          onClick={() => control("cancel")}
        >
          {t("analysis:stop")}
        </Button>
      ) : job.compatible && job.status !== "completed" && job.error !== "baseline_mismatch" ? (
        <Button icon="plus" disabled={pending} onClick={() => control("continue")}>
          {t("analysis:continue")}
        </Button>
      ) : null}
      {!job.compatible ? <p>{t("analysis:incompatible")}</p> : null}
    </div>
  )
}
