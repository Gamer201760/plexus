import { useState } from "react"
import { Link, useParams, useSearchParams } from "react-router"
import { type Mode, useRegionLinks } from "@/entities/link"
import { RegionMap, type Season, useRegion } from "@/entities/region"
import { useSettlements } from "@/entities/settlement"
import { RegionLinks } from "@/features/region-links"
import { RegionSettlements } from "@/features/region-settlements"
import { RegionSummary } from "@/features/region-summary"
import { isApiError } from "@/shared/api"
import { useDocumentTitle, useTranslation } from "@/shared/i18n"
import { EmptyState, ErrorState, Icon, PageHeader, Segmented, Skeleton } from "@/shared/ui"
import styles from "./region-page.module.css"

const MAP_LIMIT = 200
const SEASONS = ["all", "summer", "winter"] as const

export function RegionPage() {
  const { t } = useTranslation()
  const { regionId = "" } = useParams()
  const [params, setParams] = useSearchParams()
  const [season, setSeason] = useState<Season>("all")
  const [activeLink, setActiveLink] = useState<string | null>(null)
  const [modes, setModes] = useState<readonly Mode[]>([])
  const highlight = params.get("settlement")
  const region = useRegion(regionId, season)
  const links = useRegionLinks(regionId, season)
  const places = useSettlements({
    regionId,
    q: "",
    sort: "population",
    order: "desc",
    limit: MAP_LIMIT,
    offset: 0,
  })
  const data = region.data
  const allLinks = links.data ?? []
  const shown = modes.length === 0 ? allLinks : allLinks.filter((l) => modes.includes(l.mode))
  useDocumentTitle(data?.name ?? t("nav:regions"))

  if (region.isError) {
    const missing = isApiError(region.error) && region.error.kind === "notFound"
    return (
      <div className={styles.page}>
        <PageHeader title={t("region:fallbackTitle")} />
        {missing ? (
          <EmptyState icon="search" title={t("region:notFound")} />
        ) : (
          <ErrorState title={t("errors:kind.server")} onRetry={() => void region.refetch()} />
        )}
      </div>
    )
  }

  const map =
    data?.path && data.bbox ? (
      <RegionMap
        path={data.path}
        bbox={data.bbox}
        settlements={places.data?.items ?? []}
        links={shown}
        activeLinkId={activeLink}
        highlightId={highlight}
        label={t("region:map.label")}
        onLink={setActiveLink}
      />
    ) : (
      <div className={styles.mapEmpty}>
        <EmptyState icon="map" title={t("region:map.noGeometry")} />
      </div>
    )

  return (
    <div className={styles.page} aria-busy={data === undefined}>
      <nav className={styles.crumbs} aria-label={t("region:breadcrumb")}>
        <Link to="/regions" viewTransition className={styles.crumb}>
          {t("region:breadcrumb")}
        </Link>
        <Icon name="chevron-right" size="sm" />
        <span>{data?.name}</span>
      </nav>
      <PageHeader
        title={data?.name ?? t("region:fallbackTitle")}
        actions={
          <Segmented
            label={t("data:season.legend")}
            value={season}
            onChange={(next) => {
              setSeason(next)
              setModes([])
            }}
            options={SEASONS.map((key) => ({ value: key, label: t(`data:season.${key}`) }))}
          />
        }
      />
      <RegionSummary region={data} />
      <div className={styles.workspace}>
        <div className={styles.mapCell}>
          {data ? map : <Skeleton shape="block" className={styles.mapSkeleton} />}
        </div>
        <RegionLinks
          links={links.data}
          modes={modes}
          onModesChange={setModes}
          activeId={activeLink}
          onActive={setActiveLink}
        />
      </div>
      <RegionSettlements
        regionId={regionId}
        highlightId={highlight}
        onHighlight={(id) =>
          setParams({ settlement: id }, { replace: true, preventScrollReset: true })
        }
      />
    </div>
  )
}
