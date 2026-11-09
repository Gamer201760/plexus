import { useRef } from "react"
import type { Pilot } from "@/entities/pilot"
import { isApiError } from "@/shared/api"
import { useErrorText, useTranslation } from "@/shared/i18n"
import { Banner, Button, Card, EmptyState, ErrorState, Segmented } from "@/shared/ui"
import { exportComparison, exportParameters } from "./export-experiment"
import { LinkEditor } from "./link-editor"
import styles from "./pilot-experiment.module.css"
import { TripResult } from "./trip-result"
import { useExperiment } from "./use-experiment"

export interface PilotExperimentProps {
  readonly pilot: Pilot
  readonly onReload: () => Promise<boolean>
}

export function PilotExperiment({ pilot, onReload }: PilotExperimentProps) {
  const { t } = useTranslation()
  const state = useExperiment(pilot)
  const currentEvaluation = useRef(state.evaluation)
  currentEvaluation.current = state.evaluation
  const errorText = useErrorText()
  const staleVersion =
    isApiError(state.evaluation.error) && state.evaluation.error.code === "stale_pilot_version"
  const result = state.evaluation.data
  const reloadPilot = () => {
    const error = state.evaluation.error
    void onReload().then((succeeded) => {
      if (succeeded && currentEvaluation.current.error === error) currentEvaluation.current.reset()
    })
  }
  return (
    <div className={styles.experiment}>
      <Banner
        tone="warning"
        title={t("pilot:conditions")}
        description={t("pilot:conditionsDetail")}
      />
      <div className={styles.workspace}>
        <Card title={t("pilot:links")} description={t("pilot:linksHint")}>
          <Segmented
            label={t("pilot:season")}
            value={state.season}
            onChange={state.setSeason}
            options={[
              { value: "summer", label: t("pilot:summer"), icon: "sun" },
              { value: "winter", label: t("pilot:winter"), icon: "snowflake" },
            ]}
          />
          <div className={styles.actions}>
            <Button
              icon="refresh"
              pending={state.evaluation.isPending}
              disabled={!state.valid}
              onClick={state.calculate}
            >
              {t("pilot:calculate")}
            </Button>
            <Button variant="secondary" icon="retry" onClick={state.reset}>
              {t("pilot:reset")}
            </Button>
          </div>
          <ul className={styles.links}>
            {pilot.edges
              .filter((edge) => edge.edit_disabled_reason !== "derived_road_edge")
              .map((edge) => (
                <LinkEditor
                  key={edge.id}
                  pilot={pilot}
                  edge={edge}
                  season={state.season}
                  draft={
                    state.drafts[edge.id] ?? {
                      enabled: true,
                      frequency: edge.frequency_per_week?.toString() ?? "",
                    }
                  }
                  onChange={(draft) => state.update(edge.id, draft)}
                />
              ))}
          </ul>
        </Card>
        <div className={styles.results} aria-busy={state.evaluation.isPending}>
          {state.stale && (
            <Banner
              tone="warning"
              announce
              title={t("pilot:stale")}
              description={t("pilot:staleHint")}
            />
          )}
          {state.evaluation.isError && (
            <ErrorState
              title={t("pilot:errors.title")}
              description={errorText(state.evaluation.error)}
              onRetry={staleVersion ? reloadPilot : state.calculate}
            />
          )}
          {result ? (
            <>
              <div className={styles.actions}>
                <Button
                  variant="secondary"
                  icon="list"
                  onClick={() =>
                    exportComparison(pilot, result, [
                      t("pilot:from"),
                      t("pilot:to"),
                      t("pilot:season"),
                      t("pilot:baselineHours"),
                      t("pilot:changedHours"),
                      t("pilot:movement"),
                      t("pilot:waiting"),
                      t("pilot:difference"),
                      t("pilot:status"),
                      t("pilot:modelVersion"),
                      t("pilot:artifactVersion"),
                      t("pilot:parameters"),
                      t("pilot:assumptions"),
                      t("pilot:routeIds"),
                    ])
                  }
                >
                  {t("pilot:csv")}
                </Button>
                <Button
                  variant="secondary"
                  icon="database"
                  onClick={() => exportParameters(pilot, result)}
                >
                  {t("pilot:json")}
                </Button>
              </div>
              <Card title={t("pilot:result")} description={t("pilot:resultHint")}>
                {result.pairs.map((pair) => (
                  <TripResult key={pair.pair_id} pilot={pilot} result={pair} />
                ))}
                <p>{t("pilot:zero")}</p>
              </Card>
              <Card title={t("pilot:schedule")}>
                {result.waiting_sensitivity.map((item) => (
                  <p key={item.edge_id}>
                    {t("pilot:scheduleDetail", {
                      periodic: item.periodic_wait_h,
                      uniform: item.uniform_wait_h ?? 0,
                    })}
                  </p>
                ))}
                <p className={styles.version}>
                  {t("pilot:version", { version: result.model_version })}
                </p>
              </Card>
            </>
          ) : (
            !state.evaluation.isError && (
              <EmptyState
                title={t("pilot:empty")}
                description={t("pilot:emptyHint")}
                icon="route"
              />
            )
          )}
        </div>
      </div>
    </div>
  )
}
