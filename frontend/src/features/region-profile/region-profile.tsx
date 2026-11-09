import type { ReactNode } from "react"
import { Link, useSearchParams } from "react-router"
import { MiniMap, SeasonControl, useRegion, useRegions } from "@/entities/region"
import { isApiError } from "@/shared/api"
import { useNetworkMode } from "@/shared/hooks/use-network-mode"
import { useSeason } from "@/shared/hooks/use-season"
import { useTranslation } from "@/shared/i18n"
import { ButtonLink, Card, ErrorState, Icon, PageHeader, Skeleton, Tabs } from "@/shared/ui"
import { IndexCard } from "./index-card"
import { ModeChart } from "./mode-chart"
import styles from "./region-profile.module.css"
import { SeasonalLinks } from "./seasonal-links"

export interface RegionProfileProps {
  readonly regionId: string
  readonly calendar: ReactNode
}

export function RegionProfile({ regionId, calendar }: RegionProfileProps) {
  const { t } = useTranslation()
  const { season, seasonHref } = useSeason()
  const { networkMode } = useNetworkMode()
  const [params, setParams] = useSearchParams()
  const region = useRegion(regionId, season)
  const regions = useRegions(season)
  const data = region.data
  const isUgra = regionId === "71800000"
  const section =
    isUgra && params.get("section") === "winter-calendar" ? "winter-calendar" : "links"
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
  const items = [
    { value: "links", label: t("profile:links"), icon: "route" as const },
    ...(isUgra
      ? [{ value: "winter-calendar", label: t("profile:winter"), icon: "calendar" as const }]
      : []),
  ]
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
        items={items}
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
        {section === "winter-calendar" ? (
          calendar
        ) : (
          <div className={styles.workspace}>
            <div className={styles.main}>
              <IndexCard region={data} regions={regions.data ?? []} />
              <Card as="section" title={t("profile:seasons")} actions={<SeasonControl />}>
                <p className={styles.note}>
                  {t("profile:counts", {
                    summer: data.links_by_mode.reduce((s, m) => s + m.summer, 0),
                    winter: data.links_by_mode.reduce((s, m) => s + m.winter, 0),
                  })}
                </p>
                <ModeChart rows={data.links_by_mode} />
              </Card>
              <SeasonalLinks regionId={regionId} />
            </div>
            <Card
              className={styles.aside}
              title={t("profile:meaning")}
              media={<MiniMap rows={regions.data ?? []} selectedId={regionId} />}
            >
              <p>{t("profile:records")}</p>
              <p>{t("profile:isolation")}</p>
              {isUgra ? (
                <ButtonLink
                  to={seasonHref(`/regions/${regionId}?section=winter-calendar`)}
                  variant="secondary"
                  icon="calendar"
                >
                  {t("atlas:calendar")}
                </ButtonLink>
              ) : null}
            </Card>
          </div>
        )}
      </Tabs>
    </div>
  )
}
