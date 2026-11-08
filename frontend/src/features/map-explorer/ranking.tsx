import type { CSSProperties } from "react"
import { Link } from "react-router"
import type { RegionSummary } from "@/entities/region"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { formatMetric } from "./format-metric"
import { type MetricKey, metricValue } from "./metric"
import styles from "./ranking.module.css"

export interface RankingProps {
  readonly regions: readonly RegionSummary[]
  readonly metric: MetricKey
  readonly searchFor: (id: string) => string
}

const LIMIT = 8

export function Ranking({ regions, metric, searchFor }: RankingProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const ranked = regions
    .map((region) => ({ region, value: metricValue(region, metric) }))
    .filter((row): row is { region: RegionSummary; value: number } => row.value !== null)
    .sort((a, b) => b.value - a.value)
    .slice(0, LIMIT)
  const top = ranked[0]?.value ?? 1
  return (
    <section className={styles.ranking} aria-label={t(`data:metric.${metric}`)}>
      <p className={styles.panelSub}>{t(`data:metric.${metric}`)}</p>
      <ol className={styles.rankList}>
        {ranked.map(({ region, value }, index) => (
          <li key={region.id} style={{ "--i": index } as CSSProperties}>
            <Link
              to={{ search: searchFor(region.id) }}
              replace
              preventScrollReset
              state={{ reveal: true }}
              className={styles.rankRow}
            >
              <span className={styles.rankName}>{region.name}</span>
              <span className={styles.rankValue}>{formatMetric(value, metric, f)}</span>
              <span
                className={styles.rankBar}
                style={{ "--v": top > 0 ? value / top : 0 } as CSSProperties}
                aria-hidden="true"
              />
            </Link>
          </li>
        ))}
      </ol>
    </section>
  )
}
