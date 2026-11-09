import { IndexCoverage, type RegionDetail, type RegionSummary } from "@/entities/region"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Banner, Card, RankStrip, Stat } from "@/shared/ui"
import styles from "./index-card.module.css"

export interface IndexCardProps {
  readonly region: Pick<
    RegionDetail,
    "hansen" | "index_population_coverage" | "index_model_version"
  >
  readonly regions: readonly RegionSummary[]
}

export function IndexCard({ region, regions }: IndexCardProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  if (region.hansen === null)
    return (
      <Card as="section" title={t("region:index.title")}>
        <Banner tone="info" title={t("map:index.missing")} />
      </Card>
    )
  const values = regions.map((row) => row.hansen).filter((value): value is number => value !== null)
  const rank = 1 + values.filter((value) => value > (region.hansen ?? 0)).length
  return (
    <Card as="section" title={t("region:index.title")}>
      <div className={styles.stats}>
        <Stat label={t("data:metric.hansen")} value={f.number(region.hansen, 2)} />
        <Stat
          label={t("data:network.coverageColumn")}
          value={<IndexCoverage value={region.index_population_coverage} compact />}
        />
        <Stat
          label={t("region:index.rankLabel")}
          value={t("region:index.rank", { rank, total: values.length })}
        />
      </div>
      <RankStrip
        values={values}
        current={region.hansen}
        label={t("region:index.strip")}
        lowLabel={t("region:index.low")}
        highLabel={t("region:index.high")}
      />
      {region.index_model_version ? (
        <p className={styles.model}>
          {t("data:network.model", { version: region.index_model_version })}
        </p>
      ) : null}
    </Card>
  )
}
