import { useSeason } from "@/shared/hooks/use-season"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { ButtonLink, Card } from "@/shared/ui"
import { MiniMap } from "../mini-map/mini-map"
import type { RegionSummary } from "../region.queries"
import { SeasonPair } from "../season-pair/season-pair"
import styles from "./region-preview.module.css"
export interface RegionPreviewProps {
  readonly region: RegionSummary
  readonly summer: number
  readonly winter: number
  readonly rows: readonly RegionSummary[]
  readonly withMap?: boolean
}
export function RegionPreview({
  region,
  summer,
  winter,
  rows,
  withMap = true,
}: RegionPreviewProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const { seasonHref } = useSeason()
  return (
    <Card
      className={styles.preview}
      title={region.name}
      media={
        withMap ? (
          <>
            <MiniMap rows={rows} selectedId={region.id} />
            <p className={styles.caption}>{t("atlas:selected")}</p>
          </>
        ) : undefined
      }
    >
      <SeasonPair summer={summer} winter={winter} />
      <dl>
        {(["links_season", "population", "settlements"] as const).map((key) => (
          <div key={key}>
            <dt>{t(`atlas:facts.${key}`)}</dt>
            <dd>{key === "population" ? f.compact(region[key]) : f.integer(region[key])}</dd>
          </div>
        ))}
      </dl>
      <ButtonLink to={seasonHref(`/regions/${region.id}`)} icon="arrow-right">
        {t("map:selected.open")}
      </ButtonLink>
      {region.id === "71800000" ? (
        <ButtonLink
          to={seasonHref(`/regions/${region.id}?section=winter-calendar`)}
          variant="secondary"
          icon="calendar"
        >
          {t("atlas:calendar")}
        </ButtonLink>
      ) : null}
    </Card>
  )
}
