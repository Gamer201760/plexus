import { useSeason } from "@/shared/hooks/use-season"
import { useTranslation } from "@/shared/i18n"
import { Icon } from "@/shared/ui"
import { useRegions } from "../region.queries"
import styles from "./season-summary.module.css"
export function SeasonSummary() {
  const { t } = useTranslation()
  const { season } = useSeason()
  const summer = useRegions("summer")
  const winter = useRegions("winter")
  if (!summer.data || !winter.data) return null
  const selected = season === "summer" ? summer.data : winter.data
  const winters = new Map(winter.data.map((r) => [r.id, r.links_season]))
  const losses = summer.data.filter((r) => (winters.get(r.id) ?? 0) < r.links_season / 2).length
  return (
    <div className={styles.summary}>
      <Icon name={season === "summer" ? "sun" : "snowflake"} />
      <span>
        {t("atlas:summary", {
          season: t(`data:season.${season}`),
          count: selected.reduce((s, r) => s + r.links_season, 0),
        })}{" "}
        {t("atlas:lossSummary", { count: losses })}
      </span>
      <small>{t("atlas:caution")}</small>
    </div>
  )
}
