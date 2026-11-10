import { useQueries } from "@tanstack/react-query"
import { useEffect, useMemo, useRef } from "react"
import type { CalculationHandler, ChatCalculation } from "@/shared/api/chat-calculation"
import { api, unwrap } from "@/shared/api/client"
import { useTranslation } from "@/shared/i18n"
import { Button } from "@/shared/ui"
import { CalculationRegion } from "./calculation-region"
import styles from "./chat-calculation.module.css"
import { corridorPaths } from "./corridor-paths"

export interface ChatCalculationCardProps {
  readonly calculation: ChatCalculation
  readonly onShow?: CalculationHandler | undefined
}

export function ChatCalculationCard({ calculation, onShow }: ChatCalculationCardProps) {
  const { t } = useTranslation()
  const shown = useRef(false)
  useEffect(() => {
    if (shown.current || !onShow) return
    shown.current = true
    onShow(calculation)
  }, [calculation, onShow])
  const jobs = useQueries({
    queries: calculation.job_ids.map((id) => ({
      queryKey: ["road-scenario", id],
      queryFn: ({ signal }: { signal: AbortSignal }) =>
        unwrap(
          api.GET("/api/v1/road-scenarios/{job_id}", { signal, params: { path: { job_id: id } } }),
        ),
      refetchInterval: (query: { state: { data: { status: string } | undefined } }) =>
        ["completed", "cancelled", "failed"].includes(query.state.data?.status ?? "")
          ? false
          : 1500,
    })),
  })
  const paths = useMemo(
    () => [...new Set(corridorPaths(calculation.corridor.lines))],
    [calculation.corridor.lines],
  )
  const busy = jobs.some(
    (query) => !query.isError && (!query.data || ["queued", "running"].includes(query.data.status)),
  )
  return (
    <section className={styles.calculation} aria-label={t("chat:calculation.title")}>
      <strong>
        {t("chat:calculation.title")}: {calculation.corridor.road_ref}
      </strong>
      <div className={styles.endpoints}>
        <span>{calculation.corridor.origin}</span>
        <span>{calculation.corridor.destination}</span>
      </div>
      <svg
        className={styles.preview}
        viewBox="0 0 320 160"
        role="img"
        aria-label={t("chat:calculation.geometry")}
      >
        <g className={styles.route}>
          {paths.map((path) => (
            <path key={path} d={path} />
          ))}
        </g>
        {busy ? (
          <g className={styles.pulse}>
            {paths.map((path) => (
              <path key={path} d={path} />
            ))}
          </g>
        ) : null}
      </svg>
      <p className={styles.note}>
        {t("chat:calculation.scope", { count: calculation.corridor.way_ids.length })}
      </p>
      <Button
        variant="secondary"
        icon="map"
        disabled={!onShow}
        onClick={(event) => onShow?.(calculation, event.detail === 0)}
      >
        {t("chat:calculation.show")}
      </Button>
      {jobs.map((query, index) => (
        <CalculationRegion
          key={calculation.job_ids[index]}
          query={query}
          name={calculation.corridor.regions[index]?.name}
        />
      ))}
      <p className={styles.note}>{t("chat:calculation.limit")}</p>
    </section>
  )
}
