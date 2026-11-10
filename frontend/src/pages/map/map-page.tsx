import { MapChat } from "@/features/map-chat"
import { MapExplorer } from "@/features/map-explorer"
import { AnalysisWorkspace } from "@/features/road-analysis"
import { RoadScenario } from "@/features/road-scenario"
import { useDocumentTitle, useTranslation } from "@/shared/i18n"

export function MapPage() {
  const { t } = useTranslation()
  useDocumentTitle(null)
  return (
    <>
      <h1 className="visually-hidden" tabIndex={-1}>
        {t("map:title")}
      </h1>
      <MapExplorer
        renderPanel={(summary, context, onMapCommand, roads) => (
          <MapChat
            scenario={
              <AnalysisWorkspace
                regionId={context.region_id ?? null}
                onOverlay={roads.setAnalysisOverlay}
                manual={<RoadScenario roads={roads} context={context} />}
              />
            }
            summary={summary}
            context={context}
            onMapCommand={onMapCommand}
            onCalculation={roads.showCalculation}
          />
        )}
      />
    </>
  )
}
