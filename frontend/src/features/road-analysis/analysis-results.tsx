import type { RoadAnalysisState } from "@/entities/road-analysis"
import type { AnalysisOverlay } from "@/shared/api/road-analysis"
import { useTranslation } from "@/shared/i18n"
import { Banner, Button, Skeleton } from "@/shared/ui"
import { AnalysisDetail } from "./analysis-detail"
import { AnalysisProgress } from "./analysis-progress"
import { AnalysisRanking } from "./analysis-ranking"
import styles from "./road-analysis.module.css"

export function AnalysisResults({
  analysis,
  onOverlay,
}: {
  readonly analysis: RoadAnalysisState
  readonly onOverlay: (overlay: AnalysisOverlay | null) => void
}) {
  const { t } = useTranslation()
  const job = analysis.job
  if (!job) return null
  return (
    <>
      <strong>{job.region}</strong>
      <p>
        {t(job.mode === "criticality" ? "analysis:closureSpec" : "analysis:improvementSpec", {
          percent: job.percent,
        })}
      </p>
      <AnalysisProgress
        job={job}
        busy={analysis.busy}
        pending={analysis.control.isPending}
        control={(action) => analysis.control.mutate(action)}
      />
      {job.error ? (
        <Banner
          tone="danger"
          title={t(
            job.error === "baseline_mismatch" ? "analysis:baselineMismatch" : "analysis:failed",
          )}
        />
      ) : null}
      {job.failures.length ? <p>{t("analysis:failures", { count: job.failures.length })}</p> : null}
      <AnalysisRanking job={job} selectedWay={analysis.selectedWay} onSelect={analysis.selectWay} />
      {analysis.detail.isFetching ? <Skeleton lines={3} /> : null}
      {analysis.detail.isError ? (
        <Banner
          tone="danger"
          title={t("analysis:requestError")}
          action={
            <Button icon="retry" onClick={() => analysis.detail.refetch()}>
              {t("analysis:retry")}
            </Button>
          }
        />
      ) : null}
      {analysis.detail.data ? (
        <AnalysisDetail
          key={`${job.id}-${analysis.detail.data.result.candidate.way_id}`}
          detail={analysis.detail.data}
          onOverlay={onOverlay}
        />
      ) : null}
      <p className={styles.note}>{t("analysis:modelLimit")}</p>
    </>
  )
}
