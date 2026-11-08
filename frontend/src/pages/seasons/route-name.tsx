import { Fragment } from "react"
import { useTranslation } from "@/shared/i18n"
import { Icon, NoValue } from "@/shared/ui"
import styles from "./route-name.module.css"
import { routeStops } from "./season-time"

export interface RouteNameProps {
  readonly route: string | null
}

export function RouteName({ route }: RouteNameProps) {
  const { t } = useTranslation()
  const stops = routeStops(route)
  if (stops.length === 0) return <NoValue />
  return (
    <span className={styles.route}>
      {stops.map((stop, index) => (
        <Fragment key={stop.key}>
          {index > 0 ? (
            <Icon name="arrow-right" size="sm" label={t("seasons:to")} className={styles.arrow} />
          ) : null}
          <span className={styles.stop}>{stop.name}</span>
        </Fragment>
      ))}
    </span>
  )
}
