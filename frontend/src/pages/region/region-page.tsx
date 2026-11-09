import { useParams, useSearchParams } from "react-router"
import { pilotIdForRegion, usePilots } from "@/entities/pilot"
import { useRegion } from "@/entities/region"
import { PilotScenarios } from "@/features/pilot-experiment"
import { RegionProfile } from "@/features/region-profile"
import { RegionSettlements } from "@/features/region-settlements"
import { RegionSummary } from "@/features/region-summary"
import { WinterCalendar } from "@/features/winter-calendar"
import { useSeason } from "@/shared/hooks/use-season"
import { useDocumentTitle, useTranslation } from "@/shared/i18n"
import { Disclosure } from "@/shared/ui"
import styles from "./region-page.module.css"

export function RegionPage() {
  const { regionId = "" } = useParams()
  const { season } = useSeason()
  const [params, setParams] = useSearchParams()
  const highlight = params.get("settlement")
  const { data } = useRegion(regionId, season)
  const pilots = usePilots()
  const pilotId = pilotIdForRegion(regionId, pilots.data)
  const { t } = useTranslation()
  useDocumentTitle(data?.name ?? t("region:fallbackTitle"))
  return (
    <div className={styles.page}>
      <RegionProfile
        regionId={regionId}
        calendar={<WinterCalendar />}
        scenarios={pilotId === null ? null : <PilotScenarios pilotId={pilotId} />}
      />
      {data ? (
        <Disclosure
          key={highlight ?? "settlements"}
          title={t("region:settlements.title")}
          defaultOpen={highlight !== null}
        >
          <RegionSummary region={data} />
          <RegionSettlements
            regionId={regionId}
            highlightId={highlight}
            onHighlight={(id) =>
              setParams(
                (current) => {
                  const p = new URLSearchParams(current)
                  p.set("settlement", id)
                  return p
                },
                { replace: true, preventScrollReset: true },
              )
            }
          />
        </Disclosure>
      ) : null}
    </div>
  )
}
