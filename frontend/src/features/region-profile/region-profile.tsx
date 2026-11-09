import type { ReactNode } from "react"
import { Link, useSearchParams } from "react-router"
import { useRegion } from "@/entities/region"
import { isApiError } from "@/shared/api"
import { useNetworkMode } from "@/shared/hooks/use-network-mode"
import { useSeason } from "@/shared/hooks/use-season"
import { type MessageKey, useTranslation } from "@/shared/i18n"
import {
  ButtonLink,
  ErrorState,
  Icon,
  type IconName,
  PageHeader,
  Skeleton,
  Tabs,
} from "@/shared/ui"
import { LinksWorkspace } from "./links-workspace"
import styles from "./region-profile.module.css"

export interface RegionProfileProps {
  readonly regionId: string
  readonly calendar: ReactNode
  readonly scenarios?: ReactNode
}

type Section = "links" | "scenarios" | "winter-calendar"

function resolveSection(requested: string | null, isUgra: boolean, hasScenarios: boolean): Section {
  if (isUgra && requested === "winter-calendar") return "winter-calendar"
  if (hasScenarios && requested === "scenarios") return "scenarios"
  return "links"
}

function sectionItems(
  isUgra: boolean,
  hasScenarios: boolean,
): readonly { value: Section; label: MessageKey; icon: IconName }[] {
  return [
    { value: "links", label: "profile:links", icon: "route" },
    ...(hasScenarios
      ? ([{ value: "scenarios", label: "profile:scenarios", icon: "compare" }] as const)
      : []),
    ...(isUgra
      ? ([{ value: "winter-calendar", label: "profile:winter", icon: "calendar" }] as const)
      : []),
  ]
}

export function RegionProfile({ regionId, calendar, scenarios }: RegionProfileProps) {
  const { t } = useTranslation()
  const { season, seasonHref } = useSeason()
  const { networkMode } = useNetworkMode()
  const [params, setParams] = useSearchParams()
  const region = useRegion(regionId, season)
  const data = region.data
  const isUgra = regionId === "71800000"
  const hasScenarios = scenarios !== null && scenarios !== undefined
  const section = resolveSection(params.get("section"), isUgra, hasScenarios)
  if (region.isError)
    return (
      <ErrorState
        title={t(
          isApiError(region.error) && region.error.status === 404
            ? "region:notFound"
            : "errors:kind.server",
        )}
        onRetry={() => void region.refetch()}
      />
    )
  if (!data || data.id !== regionId) return <Skeleton lines={12} />
  const content: Record<Section, ReactNode> = {
    links: <LinksWorkspace regionId={regionId} data={data} isUgra={isUgra} />,
    scenarios,
    "winter-calendar": calendar,
  }
  return (
    <div className={styles.profile}>
      <Link to={seasonHref("/")} className={styles.back}>
        <Icon name="arrow-left" size="sm" />
        {t("region:backToMap")}
      </Link>
      <PageHeader
        title={data.name}
        actions={
          <ButtonLink
            to={`/compare?ids=${data.id}&season=${season}&network_mode=${networkMode}`}
            variant="secondary"
            icon="compare"
          >
            {t("region:compare")}
          </ButtonLink>
        }
      />
      <Tabs
        label={t("profile:sections")}
        items={sectionItems(isUgra, hasScenarios).map((item) => ({
          ...item,
          label: t(item.label),
        }))}
        value={section}
        onChange={(next) =>
          setParams(
            (current) => {
              const p = new URLSearchParams(current)
              p.set("section", next)
              return p
            },
            { preventScrollReset: true },
          )
        }
      >
        {content[section]}
      </Tabs>
    </div>
  )
}
