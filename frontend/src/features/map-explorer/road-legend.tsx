import type { RoadGraphState } from "@/entities/road-graph"
import { useTranslation } from "@/shared/i18n"
import { Button, Checkbox } from "@/shared/ui"

export function RoadLegend({ roads }: { readonly roads: RoadGraphState }) {
  const { t } = useTranslation()
  return (
    <>
      <Checkbox label={t("graph:layer")} checked={roads.enabled} onChange={roads.setEnabled} />
      {roads.hasOverlay ? (
        <Button variant="ghost" icon="minus" onClick={roads.clearOverlays}>
          {t("graph:clearMap")}
        </Button>
      ) : null}
    </>
  )
}
