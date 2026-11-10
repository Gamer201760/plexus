import type { ReactNode } from "react"
import { useSearchParams } from "react-router"
import type { AnalysisOverlay } from "@/shared/api/road-analysis"
import { useTranslation } from "@/shared/i18n"
import { useInputModality } from "@/shared/motion"
import { Select } from "@/shared/ui"
import { AnalysisPanel } from "./analysis-panel"
import styles from "./road-analysis.module.css"

interface AnalysisWorkspaceProps {
  readonly manual: ReactNode
  readonly regionId: string | null
  readonly onOverlay: (overlay: AnalysisOverlay | null) => void
}

export function AnalysisWorkspace({ manual, regionId, onOverlay }: AnalysisWorkspaceProps) {
  const { t } = useTranslation()
  const modality = useInputModality()
  const [params, setParams] = useSearchParams()
  const rawMode = params.get("analysis_mode")
  const mode =
    rawMode === "improvement" || rawMode === "criticality"
      ? rawMode
      : params.has("analysis")
        ? "criticality"
        : "manual"
  const setMode = (value: string) =>
    setParams(
      (current) => {
        const next = new URLSearchParams(current)
        next.delete("analysis")
        next.set("analysis_mode", value)
        return next
      },
      { replace: true },
    )
  return (
    <fieldset
      aria-label={t("analysis:title")}
      className={styles.workspace}
      data-instant={modality.instant}
      onKeyDown={modality.onKeyDown}
      onPointerDown={modality.onPointerDown}
    >
      <div className={styles.controls}>
        <Select
          label={t("analysis:mode")}
          value={mode}
          onChange={(value) => {
            setMode(value)
            onOverlay(null)
          }}
          options={[
            { value: "manual", label: t("analysis:manual") },
            { value: "criticality", label: t("analysis:criticality") },
            { value: "improvement", label: t("analysis:improvement") },
          ]}
        />
      </div>
      {mode === "manual" ? (
        manual
      ) : (
        <AnalysisPanel
          key={`${regionId}-${mode}`}
          regionId={regionId}
          mode={mode}
          onOverlay={onOverlay}
        />
      )}
    </fieldset>
  )
}
