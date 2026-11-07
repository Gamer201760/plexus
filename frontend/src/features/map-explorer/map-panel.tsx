import type { IndexStatus } from "@/entities/reference"
import { type Overview, type RegionSummary, type Season, useRegion } from "@/entities/region"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Banner, ButtonLink, Card, CloseButton, ScrollArea, Skeleton, Stat } from "@/shared/ui"
import { TransportIcon } from "@/shared/ui/brand"
import styles from "./map-panel.module.css"
import type { MetricKey } from "./metric"
import { Ranking } from "./ranking"

export interface MapPanelProps {
  readonly overview: Overview
  readonly regions: readonly RegionSummary[]
  readonly metric: MetricKey
  readonly season: Season
  readonly selectedId: string | null
  readonly onClear: () => void
}

function IndexBanner({ index }: { readonly index: IndexStatus }) {
  const { t } = useTranslation()
  if (index.status === "ready") return null
  return (
    <Banner
      tone="info"
      title={t("map:index.missing")}
      description={t("map:index.missingText")}
      action={
        <ButtonLink to="/method" variant="secondary" size="compact" icon="book">
          {t("map:index.method")}
        </ButtonLink>
      }
    />
  )
}

interface SelectedProps {
  readonly id: string
  readonly season: Season
  readonly onClose: () => void
}

function SelectedRegion({ id, season, onClose }: SelectedProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const { data } = useRegion(id, season)
  if (!data) return <Skeleton lines={6} />
  return (
    <Card
      as="section"
      key={data.id}
      title={data.name}
      actions={<CloseButton label={t("map:selected.close")} onClick={onClose} />}
      className={`${styles.flat} ${styles.selected}`}
    >
      <div className={styles.stats}>
        <Stat label={t("map:selected.settlements")} value={f.integer(data.settlements)} />
        <Stat label={t("map:selected.population")} value={f.compact(data.population)} />
        <Stat label={t("map:selected.links")} value={f.integer(data.links_season)} />
        <Stat
          label={t("map:selected.companies")}
          value={data.companies === null ? t("map:legend.none") : f.compact(data.companies)}
        />
      </div>
      {data.links_by_mode.length > 0 ? (
        <ul className={styles.modes}>
          {data.links_by_mode.map((row) => (
            <li key={row.mode} className={styles.modeRow}>
              <TransportIcon mode={row.mode} size="sm" />
              <span>{t(`data:mode.${row.mode}`)}</span>
              <span className={styles.modeValue}>{f.integer(row[season])}</span>
            </li>
          ))}
        </ul>
      ) : null}
      <ButtonLink to={`/regions/${data.id}`} icon="arrow-right">
        {t("map:selected.open")}
      </ButtonLink>
    </Card>
  )
}

export function MapPanel({
  overview,
  regions,
  metric,
  season,
  selectedId,
  onClear,
}: MapPanelProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  return (
    <aside className={styles.panel} aria-live="polite">
      <ScrollArea className={styles.scroll} label={t("map:overview.title")}>
        <div className={styles.content}>
          {selectedId ? (
            <SelectedRegion id={selectedId} season={season} onClose={onClear} />
          ) : (
            <Card as="section" title={t("map:overview.title")} className={styles.flat}>
              <div className={styles.stats}>
                <Stat
                  label={t("map:overview.settlements")}
                  value={f.integer(overview.settlements)}
                />
                <Stat label={t("map:overview.population")} value={f.compact(overview.population)} />
                <Stat label={t("map:overview.links")} value={f.integer(overview.links)} />
                <Stat label={t("map:overview.regions")} value={f.integer(overview.regions)} />
              </div>
            </Card>
          )}
          <IndexBanner index={overview.index} />
          <Ranking regions={regions} metric={metric} />
        </div>
      </ScrollArea>
    </aside>
  )
}
