import type { CSSProperties } from "react"
import type { WinterRoad } from "@/entities/reference"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Disclosure, NoValue } from "@/shared/ui"
import styles from "./calendar-row.module.css"
import { calendarMonths, calendarPosition } from "./calendar-time"

interface CalendarRowProps {
  readonly road: WinterRoad
  readonly previous: WinterRoad | undefined
  readonly year: number
}
function Bar({
  road,
  year,
  previous = false,
}: {
  readonly road: WinterRoad | undefined
  readonly year: number
  readonly previous?: boolean
}) {
  if (!road?.opening_date || !(road.closure_date ?? road.report_date)) return null
  const from = calendarPosition(year, road.opening_date)
  const to = calendarPosition(year, road.closure_date ?? road.report_date ?? road.opening_date)
  return (
    <span
      className={styles.bar}
      data-previous={previous}
      data-open={!road.closure_date}
      style={
        { "--bar-left": `${from}%`, "--bar-width": `${Math.max(0, to - from)}%` } as CSSProperties
      }
    />
  )
}
function Facts({ road }: { readonly road: WinterRoad }) {
  const { t } = useTranslation()
  const f = useFormatters()
  return (
    <div className={styles.facts}>
      <strong>
        {t("calendar:year", {
          from: String((road.season_end_year ?? 1) - 1),
          to: String(road.season_end_year),
        })}
      </strong>
      <dl>
        {(["opening_date", "closure_date", "report_date"] as const).map((key) => (
          <div key={key}>
            <dt>{t(`calendar:${key}`)}</dt>
            <dd>{road[key] ? f.date(road[key]) : t("calendar:unknown")}</dd>
          </div>
        ))}
        <div>
          <dt>{t("seasons:weight")}</dt>
          <dd>
            {road.weight_limit_tonnes === null ? (
              <NoValue />
            ) : (
              t("calendar:tonnes", { value: road.weight_limit_tonnes })
            )}
          </dd>
        </div>
        <div>
          <dt>{t("data:source")}</dt>
          <dd>{road.source_file ?? <NoValue />}</dd>
        </div>
      </dl>
    </div>
  )
}
export function CalendarRow({ road, previous, year }: CalendarRowProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  return (
    <Disclosure
      className={styles.row}
      title={
        <span className={styles.summary}>
          <span className={styles.name}>
            <strong>{road.route ?? t("seasons:route")}</strong>
            <small>
              {road.road_km === null ? <NoValue /> : t("calendar:km", { value: road.road_km })}
            </small>
          </span>
          <span className={styles.track} data-compare={!!previous} aria-hidden="true">
            {calendarMonths(year).map((m) => (
              <i
                key={m.key}
                className={styles.guide}
                style={{ "--tick-left": `${m.at}%` } as CSSProperties}
              />
            ))}
            <Bar road={road} year={year} />
            <Bar road={previous} year={year} previous />
          </span>
          <span className={styles.dates}>
            <span>{road.opening_date ? f.date(road.opening_date) : t("calendar:unknown")}</span>
            <span>
              {(road.closure_date ?? road.report_date)
                ? f.date(road.closure_date ?? road.report_date ?? "")
                : t("calendar:unknown")}
              <small>
                {road.closure_date ? t("calendar:closure_date") : t("calendar:reportEnd")}
              </small>
            </span>
          </span>
        </span>
      }
    >
      <div className={styles.details}>
        <Facts road={road} />
        {previous ? <Facts road={previous} /> : null}
        <p>{t("calendar:limit")}</p>
      </div>
    </Disclosure>
  )
}
