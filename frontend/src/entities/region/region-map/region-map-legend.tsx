import { useTranslation } from "@/shared/i18n"
import type { MapLink, MapMode } from "./region-map-geometry"
import styles from "./region-map-legend.module.css"

export interface RegionMapLegendProps {
  readonly modes: readonly MapMode[]
  readonly links: readonly MapLink[]
}

export function RegionMapLegend({ modes, links }: RegionMapLegendProps) {
  const { t } = useTranslation()
  const winter = links.some((link) => link.season === "winter")
  const unknown = links.some((link) => link.season === null)
  return (
    <figcaption className={styles.legend}>
      <ul className={styles.items} aria-label={t("region:map.legend.title")}>
        {modes.map((mode) => (
          <li key={mode} className={styles.item}>
            <span className={styles.swatch} data-mode={mode} aria-hidden="true" />
            {t(`data:mode.${mode}`)}
          </li>
        ))}
        {winter ? (
          <li className={styles.item}>
            <span className={styles.swatch} data-dash="winter" aria-hidden="true" />
            {t("region:map.legend.winter")}
          </li>
        ) : null}
        {unknown ? (
          <li className={styles.item}>
            <span className={styles.swatch} data-dash="unknown" aria-hidden="true" />
            {t("data:season.unknown")}
          </li>
        ) : null}
        {modes.length > 0 ? (
          <li className={styles.item}>
            <span className={styles.end} aria-hidden="true" />
            {t("region:map.legend.ends")}
          </li>
        ) : null}
        <li className={styles.item}>
          <span className={styles.dots} aria-hidden="true">
            <span className={styles.dot} data-size="sm" />
            <span className={styles.dot} data-size="lg" />
          </span>
          {t("region:map.legend.places")}
        </li>
      </ul>
    </figcaption>
  )
}
