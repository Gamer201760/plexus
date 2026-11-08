import { useRegionLinks } from "@/entities/link"
import { useSeason } from "@/shared/hooks/use-season"
import { useTranslation } from "@/shared/i18n"
import { ButtonLink, Card, EmptyState, ErrorState, Icon, Skeleton } from "@/shared/ui"
import { TransportIcon } from "@/shared/ui/brand"
import styles from "./seasonal-links.module.css"
export function SeasonalLinks({ regionId }: { readonly regionId: string }) {
  const { t } = useTranslation()
  const { season } = useSeason()
  const links = useRegionLinks(regionId, season)
  const rows = (links.data ?? []).filter((l) => l.season === season)
  if (links.isError)
    return <ErrorState title={t("errors:kind.server")} onRetry={() => void links.refetch()} />
  if (!links.data) return <Skeleton lines={4} />
  return (
    <Card
      title={t("profile:onlySeason")}
      description={t("profile:onlyNote", { season: t(`data:season.${season}`) })}
    >
      {rows.length ? (
        <div className={styles.links}>
          {rows.map((l) => (
            <div key={l.id}>
              <TransportIcon mode={l.mode} size="sm" />
              <span>
                {l.from.name}
                <Icon name="arrow-right" size="sm" />
                {l.to.name}
              </span>
              <small>{t(`data:season.${season}`)}</small>
              {l.source_url ? (
                <ButtonLink to={l.source_url} icon="external" variant="ghost">
                  <span className="visually-hidden">{t("data:openSource")}</span>
                </ButtonLink>
              ) : null}
            </div>
          ))}
        </div>
      ) : (
        <EmptyState icon="route" title={t("profile:empty")} />
      )}
    </Card>
  )
}
