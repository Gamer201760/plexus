import type { Pilot, PilotPairResult } from "@/entities/pilot"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Banner, DataTable, Disclosure, NoValue } from "@/shared/ui"
import styles from "./trip-result.module.css"

export interface TripResultProps {
  readonly pilot: Pilot
  readonly result: PilotPairResult
}

export function TripResult({ pilot, result }: TripResultProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const pair = pilot.pairs.find((item) => item.id === result.pair_id)
  const name = (id: string | undefined) => pilot.points.find((point) => point.id === id)?.name ?? id
  const value = (hours: number | null) => (hours === null ? <NoValue /> : f.number(hours, 2))
  const rows = [
    { id: "baseline", route: result.baseline },
    { id: "changed", route: result.changed },
  ] as const
  const title = t("pilot:routeTitle", { from: name(pair?.from_id), to: name(pair?.to_id) })
  return (
    <article className={styles.trip} aria-label={title}>
      <p className={styles.title}>{title}</p>
      <DataTable
        caption={title}
        rows={rows}
        rowKey={(row) => row.id}
        columns={[
          { key: "variant", header: t("pilot:variant"), cell: (row) => t(`pilot:${row.id}`) },
          {
            key: "total",
            header: t("pilot:total"),
            numeric: true,
            cell: (row) => value(row.route.total_h),
          },
          {
            key: "travel",
            header: t("pilot:movement"),
            numeric: true,
            cell: (row) => value(row.route.travel_h),
          },
          {
            key: "waiting",
            header: t("pilot:waiting"),
            numeric: true,
            cell: (row) => value(row.route.waiting_h),
          },
        ]}
      />
      <p className={styles.delta}>
        {t("pilot:difference")}: {value(result.delta_h)}
      </p>
      <p>{t(`pilot:${result.changed.status}`)}</p>
      {result.changed.warnings.length > 0 && (
        <Banner tone="warning" title={t("pilot:incomplete")} />
      )}
      {result.optimistic_changed.total_h !== null && (
        <p className={styles.note}>
          {t("pilot:optimistic", { value: result.optimistic_changed.total_h })}
        </p>
      )}
      <Disclosure title={t("pilot:path")}>
        <div className={styles.details}>
          <p>
            {t("pilot:stops")}: {f.list(result.changed.point_ids.map((id) => name(id) ?? id))}
          </p>
          {result.changed.edge_ids.map((id) => {
            const edge = pilot.edges.find((item) => item.id === id)
            return (
              edge && (
                <a key={id} href={edge.source_url} target="_blank" rel="noreferrer">
                  {t("pilot:source")}: {name(edge.from_id)}, {name(edge.to_id)}
                </a>
              )
            )
          })}
          {result.changed.assumptions.some((note) => note.startsWith("assumed_frequency:")) && (
            <p>{t("pilot:assumed")}</p>
          )}
        </div>
      </Disclosure>
    </article>
  )
}
