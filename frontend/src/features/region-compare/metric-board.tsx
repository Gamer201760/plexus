import { Link } from "react-router"
import type { RegionSummary } from "@/entities/region"
import { useSeason } from "@/shared/hooks/use-season"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { BarChart, type BarChartItem, Card, NoValue, type SeriesSlot } from "@/shared/ui"
import { COMPARE_METRICS, type CompareMetric } from "./compare-metrics"
import styles from "./metric-board.module.css"

export interface MetricBoardProps {
  readonly rows: readonly RegionSummary[]
}

function toSlot(index: number): SeriesSlot {
  const slot = index + 1
  return slot === 2 || slot === 3 || slot === 4 ? slot : 1
}

export function MetricBoard({ rows }: MetricBoardProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const { seasonHref } = useSeason()
  const items = (metric: CompareMetric): BarChartItem[] =>
    rows.map((region, index) => {
      const value = metric.value(region)
      return {
        key: region.id,
        label: (
          <Link
            to={seasonHref(`/regions/${region.id}`)}
            className={styles.regionLink}
            aria-label={t("compare:open", { name: region.name })}
          >
            {region.name}
          </Link>
        ),
        value,
        display: value === null ? <NoValue /> : metric.format(value, f),
        series: toSlot(index),
      }
    })
  return (
    <div className={styles.board}>
      {COMPARE_METRICS.map((metric, index) => (
        <Card key={metric.key} as="section" title={t(metric.label)} motionIndex={index}>
          <BarChart items={items(metric)} label={t(metric.label)} swatches />
        </Card>
      ))}
    </div>
  )
}
