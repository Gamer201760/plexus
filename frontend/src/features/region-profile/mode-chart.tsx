import type { RegionDetail } from "@/entities/region"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Icon, PairedBars } from "@/shared/ui"
import { TransportIcon } from "@/shared/ui/brand"
import styles from "./mode-chart.module.css"

export interface ModeChartProps {
  readonly rows: RegionDetail["links_by_mode"]
}

export function ModeChart({ rows }: ModeChartProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  return (
    <PairedBars
      label={t("atlas:composition")}
      legendMain={
        <>
          <Icon name="sun" size="sm" />
          {t("data:season.summer")}
        </>
      }
      legendAlt={
        <>
          <Icon name="snowflake" size="sm" />
          {t("data:season.winter")}
        </>
      }
      rows={rows.map((mode) => ({
        key: mode.mode,
        label: (
          <span className={styles.mode}>
            <TransportIcon mode={mode.mode} size="sm" />
            {t(`data:mode.${mode.mode}`)}
          </span>
        ),
        main: mode.summer,
        alt: mode.winter,
        displayMain: f.integer(mode.summer),
        displayAlt: f.integer(mode.winter),
      }))}
    />
  )
}
