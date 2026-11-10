import { useState } from "react"
import type { AnalysisOverlay, AnalysisDetail as Detail } from "@/shared/api/road-analysis"
import { useTranslation } from "@/shared/i18n"
import { Button, ScrollArea, Stat } from "@/shared/ui"
import styles from "./road-analysis.module.css"

interface AnalysisDetailProps {
  readonly detail: Detail
  readonly onOverlay: (overlay: AnalysisOverlay) => void
}

export function AnalysisDetail({ detail, onOverlay }: AnalysisDetailProps) {
  const { t } = useTranslation()
  const [limit, setLimit] = useState(50)
  const r = detail.result
  return (
    <section className={styles.detail} aria-label={r.candidate.name}>
      <strong>{r.candidate.name}</strong>
      <p>{t("analysis:way", { id: r.candidate.way_id })}</p>
      <p>{t("analysis:roadLength", { value: r.candidate.length_km })}</p>
      {r.candidate.crosses_boundary ? <p>{t("analysis:crossesBoundary")}</p> : null}
      <div className={styles.comparison}>
        <Stat label={t("analysis:before")} value={t("analysis:number", { value: r.before })} />
        <Stat label={t("analysis:after")} value={t("analysis:number", { value: r.after })} />
      </div>
      <Button
        icon="map"
        onClick={(event) => onOverlay({ detail, focus: Date.now(), instant: event.detail === 0 })}
      >
        {t("analysis:showMap")}
      </Button>
      <p className={styles.note}>{t("analysis:populationMeaning")}</p>
      <p>{t("analysis:duration", { value: r.elapsed_seconds })}</p>
      <ScrollArea orientation="horizontal" label={t("analysis:settlements")}>
        <table className={styles.table}>
          <caption>{t("analysis:settlements")}</caption>
          <thead>
            <tr>
              <th>{t("analysis:settlement")}</th>
              <th>{t("analysis:population")}</th>
              <th>{t("analysis:before")}</th>
              <th>{t("analysis:after")}</th>
            </tr>
          </thead>
          <tbody>
            {detail.settlements.slice(0, limit).map((p) => (
              <tr key={p.impact.point_id}>
                <th scope="row">
                  {p.name}
                  {p.impact.newly_isolated ? (
                    <span className={styles.note}>{t("analysis:isolated")}</span>
                  ) : null}
                </th>
                <td>{t("analysis:number", { value: p.impact.population })}</td>
                <td>{t("analysis:number", { value: p.impact.before })}</td>
                <td>{t("analysis:number", { value: p.impact.after })}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </ScrollArea>
      {!detail.settlements.length ? <p>{t("analysis:noChanges")}</p> : null}
      {limit < detail.settlements.length ? (
        <Button icon="plus" variant="secondary" onClick={() => setLimit((n) => n + 50)}>
          {t("analysis:moreSettlements")}
        </Button>
      ) : null}
    </section>
  )
}
