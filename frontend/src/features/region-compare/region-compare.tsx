import { NetworkModeControl, SeasonControl, useRegions } from "@/entities/region"
import { useSeason } from "@/shared/hooks/use-season"
import { useTranslation } from "@/shared/i18n"
import { EmptyState, ErrorState, Skeleton } from "@/shared/ui"
import { MetricBoard } from "./metric-board"
import styles from "./region-compare.module.css"
import { RegionPicker } from "./region-picker"
import { useCompareParams } from "./use-compare-params"

export function RegionCompare() {
  const { t } = useTranslation()
  const { season } = useSeason()
  const regions = useRegions(season)
  const { ids, add, remove } = useCompareParams()
  if (regions.isError)
    return <ErrorState title={t("errors:kind.server")} onRetry={() => void regions.refetch()} />
  if (!regions.data) return <Skeleton lines={10} />
  const rows = ids
    .map((id) => (regions.data ?? []).find((region) => region.id === id))
    .filter((region): region is NonNullable<typeof region> => region !== undefined)
  return (
    <div className={styles.compare}>
      <div className={styles.controls}>
        <RegionPicker regions={regions.data} ids={ids} onAdd={add} onRemove={remove} />
        <div className={styles.modes}>
          <SeasonControl />
          <NetworkModeControl />
        </div>
      </div>
      {rows.length === 0 ? (
        <EmptyState
          icon="compare"
          title={t("compare:empty")}
          description={t("compare:emptyHint")}
        />
      ) : (
        <MetricBoard rows={rows} />
      )}
    </div>
  )
}
