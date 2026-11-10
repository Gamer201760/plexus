import { useEffect, useState } from "react"
import { useRoadAnalysis } from "@/entities/road-analysis"
import type { AnalysisMode, AnalysisOverlay } from "@/shared/api/road-analysis"
import { useTranslation } from "@/shared/i18n"
import { Banner, Button, NumberField, ScrollArea, Select } from "@/shared/ui"
import { AnalysisResults } from "./analysis-results"
import styles from "./road-analysis.module.css"

interface AnalysisPanelProps {
  readonly regionId: string | null
  readonly mode: AnalysisMode
  readonly onOverlay: (overlay: AnalysisOverlay | null) => void
}

export function AnalysisPanel({ regionId, mode, onOverlay }: AnalysisPanelProps) {
  const { t } = useTranslation()
  const [percent, setPercent] = useState("20")
  const analysis = useRoadAnalysis(regionId, mode)
  const amount = Number(percent)
  const valid = Number.isInteger(amount) && amount >= 1 && amount <= 200
  const job = analysis.job
  useEffect(() => {
    if (analysis.detail.data) onOverlay({ detail: analysis.detail.data, focus: 0 })
  }, [analysis.detail.data, onOverlay])
  return (
    <ScrollArea className={styles.panel} label={t("analysis:title")}>
      <p className={styles.note}>{t("analysis:baseNetwork")}</p>
      {mode === "improvement" ? (
        <NumberField
          label={t("analysis:percent")}
          value={percent}
          onChange={(e) => setPercent(e.target.value)}
          hint={t("analysis:percentHint")}
          error={valid ? undefined : t("analysis:percentError")}
        />
      ) : null}
      {!regionId ? <p>{t("analysis:pickRegion")}</p> : null}
      <Button
        icon="search"
        disabled={!regionId || !valid || analysis.start.isPending || analysis.busy}
        onClick={() => analysis.start.mutate(amount)}
      >
        {t("analysis:start")}
      </Button>
      <p className={styles.note}>{t("analysis:waitHint")}</p>
      {analysis.recent.length ? (
        <Select
          label={t("analysis:history")}
          value={job?.id ?? ""}
          onChange={analysis.selectJob}
          options={analysis.recent.map((j) => ({
            value: j.id,
            label: `${j.region}: ${t(j.mode === "criticality" ? "analysis:criticality" : "analysis:improvement")}${j.mode === "improvement" ? ` +${j.percent}%` : ""}`,
          }))}
        />
      ) : null}
      {analysis.error ? (
        <Banner
          tone="danger"
          title={t("analysis:requestError")}
          action={
            <Button icon="retry" onClick={analysis.retry}>
              {t("analysis:retry")}
            </Button>
          }
        />
      ) : null}
      <AnalysisResults analysis={analysis} onOverlay={onOverlay} />
    </ScrollArea>
  )
}
