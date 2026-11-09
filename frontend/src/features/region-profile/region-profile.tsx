import type { ReactNode } from "react"
import { Link, useSearchParams } from "react-router"
import { MiniMap, SeasonControl, SeasonPair, useRegion, useRegions } from "@/entities/region"
import { isApiError } from "@/shared/api"
import { useSeason } from "@/shared/hooks/use-season"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { ButtonLink, Card, ErrorState, Icon, PageHeader, Skeleton, Tabs } from "@/shared/ui"
import { TransportIcon } from "@/shared/ui/brand"
import styles from "./region-profile.module.css"
import { SeasonalLinks } from "./seasonal-links"
export interface RegionProfileProps {
  readonly regionId: string
  readonly calendar: ReactNode
}
export function RegionProfile({ regionId, calendar }: RegionProfileProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const { season, seasonHref } = useSeason()
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
  const sum = (key: "summer" | "winter") => data.links_by_mode.reduce((s, m) => s + m[key], 0)
  const items = [
    { value: "links", label: t("profile:links"), icon: "route" as const },
    ...(isUgra
      ? [{ value: "winter-calendar", label: t("profile:winter"), icon: "calendar" as const }]
      : []),
  ]
  return (
    <div className={styles.profile}>
      <Link to={seasonHref("/regions")} className={styles.back}>
        <Icon name="arrow-left" size="sm" />
        {t("region:breadcrumb")}
      </Link>
      <PageHeader title={data.name} />
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
              <Card title={t("profile:seasons")} actions={<SeasonControl />}>
                <p className={styles.note}>
                  {t("profile:counts", { summer: sum("summer"), winter: sum("winter") })}
                </p>
                <SeasonPair summer={sum("summer")} winter={sum("winter")} />
                <table className={styles.modes}>
                  <caption className="visually-hidden">{t("atlas:composition")}</caption>
                  <thead>
                    <tr>
                      <th>{t("atlas:transport")}</th>
                      <th>{t("data:season.summer")}</th>
                      <th>{t("data:season.winter")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.links_by_mode.map((m) => (
                      <tr key={m.mode}>
                        <th>
                          <span>
                            <TransportIcon mode={m.mode} size="sm" />
                            {t(`data:mode.${m.mode}`)}
                          </span>
                        </th>
                        <td>{f.integer(m.summer)}</td>
                        <td>{f.integer(m.winter)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
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
