import { MiniMap, type RegionDetail, SeasonControl, useRegions } from "@/entities/region"
import { useSeason } from "@/shared/hooks/use-season"
import { useTranslation } from "@/shared/i18n"
import { ButtonLink, Card } from "@/shared/ui"
import { IndexCard } from "./index-card"
import { ModeChart } from "./mode-chart"
import styles from "./region-profile.module.css"
import { SeasonalLinks } from "./seasonal-links"

export interface LinksWorkspaceProps {
  readonly regionId: string
  readonly data: Pick<
    RegionDetail,
    "links_by_mode" | "hansen" | "index_population_coverage" | "index_model_version"
  >
  readonly isUgra: boolean
}

export function LinksWorkspace({ regionId, data, isUgra }: LinksWorkspaceProps) {
  const { t } = useTranslation()
  const { season, seasonHref } = useSeason()
  const regions = useRegions(season)
  return (
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
  )
}
