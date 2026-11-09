import { useTranslation } from "@/shared/i18n"
import { Card, EmptyState, ErrorState, Skeleton } from "@/shared/ui"
import { type Link, useRegionLinks } from "../link.queries"
import { LinkList } from "../link-list/link-list"

export interface RegionLinksProps {
  readonly regionId: string
  readonly season: NonNullable<Link["season"]>
  readonly className?: string | undefined
}
export function RegionLinks({ regionId, season, className }: RegionLinksProps) {
  const { t } = useTranslation()
  const links = useRegionLinks(regionId, season)
  return (
    <Card
      as="section"
      title={t("links:title")}
      className={className}
      description={links.data ? t("links:count", { count: links.data.length }) : undefined}
    >
      {links.isError ? (
        <ErrorState title={t("errors:kind.server")} onRetry={() => void links.refetch()} />
      ) : !links.data || links.isPlaceholderData ? (
        <Skeleton lines={6} />
      ) : links.data.length ? (
        <LinkList rows={links.data} />
      ) : (
        <EmptyState icon="route" title={t("links:empty")} />
      )}
    </Card>
  )
}
