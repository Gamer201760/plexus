import type { RegionDetail } from "@/entities/region"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { NoValue, Skeleton, Stat } from "@/shared/ui"
import styles from "./region-summary.module.css"

export interface RegionSummaryProps {
  readonly region:
    | Pick<
        RegionDetail,
        "settlements" | "population" | "links_season" | "companies" | "revenue_rub"
      >
    | undefined
}

export function RegionSummary({ region }: RegionSummaryProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  if (!region) return <Skeleton lines={2} />
  return (
    <div className={styles.stats}>
      <Stat label={t("region:stats.settlements")} value={f.integer(region.settlements)} />
      <Stat label={t("region:stats.population")} value={f.integer(region.population)} />
      <Stat label={t("region:stats.links")} value={f.integer(region.links_season)} />
      <Stat
        label={t("region:stats.companies")}
        value={region.companies === null ? <NoValue /> : f.integer(region.companies)}
      />
      <Stat
        label={t("region:stats.revenue")}
        value={region.revenue_rub === null ? <NoValue /> : f.compact(region.revenue_rub)}
        unit={region.revenue_rub === null ? undefined : t("data:unit.rub")}
      />
    </div>
  )
}
