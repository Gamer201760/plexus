import type { CSSProperties } from "react"
import type { WinterRoad } from "@/entities/reference"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Card } from "@/shared/ui"
import { RouteName } from "./route-name"
import { roadKey, roadSpan, type SeasonGroup, seasonTicks, seasonYears } from "./season-time"
import styles from "./season-timeline.module.css"

interface RoadBarProps {
  readonly road: WinterRoad
}

function RoadBar({ road }: RoadBarProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const span = roadSpan(road)
  if (span === null || road.opening_date === null) return <span className={styles.track} />
  const opened = f.date(road.opening_date)
  const text = road.closure_date
    ? t("seasons:span", { from: opened, to: f.date(road.closure_date) })
    : t("seasons:spanOpen", { from: opened })
  return (
    <span className={styles.track}>
      <span
        className={styles.bar}
        data-open={span.open || undefined}
        style={{ "--from": span.from, "--to": span.to } as CSSProperties}
      />
      <span className="visually-hidden">{text}</span>
    </span>
  )
}

export interface SeasonTimelineProps {
  readonly group: SeasonGroup
  readonly motionIndex: number
}

export function SeasonTimeline({ group, motionIndex }: SeasonTimelineProps) {
  const { t } = useTranslation()
  const ticks = seasonTicks(group.year)
  return (
    <Card
      as="section"
      title={t("seasons:winterOf", seasonYears(group.year))}
      description={t("seasons:routes", { count: group.roads.length })}
      motionIndex={motionIndex}
      className={styles.card}
    >
      <div className={styles.grid}>
        <span className={styles.axis} aria-hidden="true">
          {ticks.map((tick) => (
            <span
              key={tick.key}
              className={styles.tick}
              style={{ "--at": tick.at } as CSSProperties}
            >
              {tick.label}
            </span>
          ))}
        </span>
        <ul className={styles.rows}>
          {group.roads.map((road) => (
            <li key={roadKey(road)} className={styles.row}>
              <span className={styles.name}>
                <RouteName route={road.route} />
              </span>
              <span className={styles.lane}>
                {ticks.map((tick) => (
                  <span
                    key={tick.key}
                    className={styles.gridLine}
                    style={{ "--at": tick.at } as CSSProperties}
                  />
                ))}
                <RoadBar road={road} />
              </span>
            </li>
          ))}
        </ul>
      </div>
      <p className={styles.key}>
        <span className={styles.keyItem}>
          <span className={styles.swatch} aria-hidden="true" />
          {t("seasons:keyClosed")}
        </span>
        <span className={styles.keyItem}>
          <span className={styles.swatch} data-open="true" aria-hidden="true" />
          {t("seasons:stillOpen")}
        </span>
      </p>
    </Card>
  )
}
