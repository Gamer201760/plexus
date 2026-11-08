import clsx from "clsx"
import { useGeoRegions, useOverview, useRoutes } from "@/entities/region"
import { useTranslation } from "@/shared/i18n"
import { ButtonLink, ErrorState, Skeleton } from "@/shared/ui"
import { BrandMark } from "@/shared/ui/brand"
import styles from "./home-intro.module.css"
import { LinkAtlas } from "./link-atlas"

export function HomeIntro() {
  const { t } = useTranslation()
  const geo = useGeoRegions()
  const routes = useRoutes()
  const overview = useOverview()
  const failed = geo.isError || routes.isError || overview.isError
  const retry = () => {
    void geo.refetch()
    void routes.refetch()
    void overview.refetch()
  }

  return (
    <div className={styles.home}>
      <div className={styles.intro}>
        <div className={styles.wordmark}>
          <BrandMark size="fill" motion="enter" />
        </div>
        <h1 className={styles.title} tabIndex={-1}>
          {t("home:title")}
        </h1>
        {overview.data ? (
          <p className={styles.lead}>
            {t("home:lead", {
              links: overview.data.links,
              regions: overview.data.regions,
            })}
          </p>
        ) : (
          <Skeleton lines={2} className={styles.leadSkeleton} />
        )}
        <div className={styles.actions}>
          <ButtonLink to="/map" icon="map" className={clsx(styles.cta, styles.primary)}>
            {t("home:open")}
          </ButtonLink>
          <ButtonLink
            to="/method"
            variant="ghost"
            icon="book"
            className={clsx(styles.cta, styles.secondary)}
          >
            {t("home:method")}
          </ButtonLink>
        </div>
      </div>
      <div className={styles.stage}>
        {failed ? (
          <ErrorState title={t("home:failed")} onRetry={retry} />
        ) : geo.data && routes.data ? (
          <LinkAtlas
            geo={geo.data}
            routes={routes.data}
            label={t("home:map", { count: routes.data.length })}
          />
        ) : (
          <div className={styles.placeholder} role="status">
            <span className="visually-hidden">{t("common:state.loading")}</span>
          </div>
        )}
      </div>
    </div>
  )
}
