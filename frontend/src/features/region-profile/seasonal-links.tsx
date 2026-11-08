import { LinkList, useRegionLinks } from "@/entities/link"
import { useSeason } from "@/shared/hooks/use-season"
import { useTranslation } from "@/shared/i18n"
import { Card, EmptyState, ErrorState, Skeleton } from "@/shared/ui"
export function SeasonalLinks({ regionId }: { readonly regionId: string }) {
  const { t } = useTranslation()
  const { season } = useSeason()
  const links = useRegionLinks(regionId, season)
  const rows = (links.data ?? []).filter((link) => link.season === season)
  if (links.isError)
    return <ErrorState title={t("errors:kind.server")} onRetry={() => void links.refetch()} />
  if (!links.data) return <Skeleton lines={4} />
  return (
    <Card
      title={t("profile:onlySeason")}
      description={t("profile:onlyNote", { season: t(`data:season.${season}`) })}
    >
      {rows.length ? (
        <LinkList rows={rows} />
      ) : (
        <EmptyState icon="route" title={t("profile:empty")} />
      )}
    </Card>
  )
}
