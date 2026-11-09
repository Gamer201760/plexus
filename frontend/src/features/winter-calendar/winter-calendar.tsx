import type { CSSProperties } from "react"
import { useState } from "react"
import { useWinterRoads } from "@/entities/reference"
import { useTranslation } from "@/shared/i18n"
import { Card, Checkbox, EmptyState, ErrorState, Select, Skeleton } from "@/shared/ui"
import { CalendarRow } from "./calendar-row"
import { calendarKey, calendarMonths, calendarYears, routeRoad } from "./calendar-time"
import styles from "./winter-calendar.module.css"
export function WinterCalendar() {
  const { t } = useTranslation()
  const query = useWinterRoads()
  const [chosen, setChosen] = useState<string | null>(null)
  const [compare, setCompare] = useState(false)
  const roads = (query.data ?? []).filter((road) =>
    routeRoad(road, [t("calendar:totalLabel"), t("calendar:aggregateLabel")]),
  )
  const years = calendarYears(roads)
  const year = Number(chosen ?? years[0])
  const previousYear = years.find((y) => y !== year)
  const rows = roads.filter((r) => r.season_end_year === year)
  const districts = [...new Set(rows.map((r) => r.district))]
  if (query.isError)
    return <ErrorState title={t("errors:kind.server")} onRetry={() => void query.refetch()} />
  if (!query.data) return <Skeleton lines={10} />
  if (!years.length) return <EmptyState icon="calendar" title={t("calendar:empty")} />
  return (
    <section className={styles.calendar} aria-label={t("calendar:title")}>
      <header className={styles.toolbar}>
        <div>
          <strong className={styles.title}>{t("calendar:title")}</strong>
          <p>{t("calendar:routes", { count: rows.length })}</p>
        </div>
        <div className={styles.controls}>
          <Select
            label={t("calendar:season")}
            value={String(year)}
            onChange={setChosen}
            options={years.map((y) => ({
              value: String(y),
              label: t("calendar:year", { from: String(y - 1), to: String(y) }),
            }))}
          />
          {previousYear ? (
            <Checkbox
              label={t("calendar:compare", {
                from: String(previousYear - 1),
                to: String(previousYear),
              })}
              checked={compare}
              onChange={setCompare}
            />
          ) : null}
        </div>
      </header>
      <p className={styles.hint}>{t("calendar:hint")}</p>
      <div className={styles.legend}>
        <span>
          {t("calendar:currentBar", {
            year: t("calendar:year", { from: String(year - 1), to: String(year) }),
          })}
        </span>
        {compare && previousYear ? (
          <span>
            {t("calendar:previousBar", {
              year: t("calendar:year", {
                from: String(previousYear - 1),
                to: String(previousYear),
              }),
            })}
          </span>
        ) : null}
      </div>
      <div className={styles.schedule}>
        <div className={styles.axis}>
          <span>{t("seasons:route")}</span>
          <div>
            {calendarMonths(year).map((m) => (
              <span key={m.key} style={{ "--tick-left": `${m.at}%` } as CSSProperties}>
                {m.label}
              </span>
            ))}
          </div>
          <span>{t("calendar:dates")}</span>
        </div>
        {districts.map((district) => (
          <section key={district ?? "unknown"}>
            <Card className={styles.district} title={district ?? t("calendar:unknown")}>
              {null}
            </Card>
            {rows
              .filter((r) => r.district === district)
              .map((road) => (
                <CalendarRow
                  key={calendarKey(road)}
                  road={road}
                  year={year}
                  previous={
                    compare
                      ? roads.find(
                          (r) =>
                            calendarKey(r) === calendarKey(road) &&
                            r.season_end_year === previousYear,
                        )
                      : undefined
                  }
                />
              ))}
          </section>
        ))}
      </div>
    </section>
  )
}
