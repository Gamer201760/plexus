import type { ScenarioCatalog } from "@/entities/scenario"
import { useScenarioCatalog } from "@/entities/scenario"
import { isApiError } from "@/shared/api"
import { useErrorText, useTranslation } from "@/shared/i18n"
import { Banner, Button, Card, EmptyState, ErrorState, Segmented, Skeleton } from "@/shared/ui"
import { ImpactResults } from "./impact-results"
import { LinkBuilder } from "./link-builder"
import styles from "./scenario-lab.module.css"
import { useScenarioLab } from "./use-scenario-lab"

export function ScenarioLab() {
  const { t } = useTranslation()
  const catalog = useScenarioCatalog()
  const errorText = useErrorText()
  if (catalog.isError)
    return (
      <ErrorState
        title={t("scenario:errors.title")}
        description={errorText(catalog.error)}
        onRetry={() => void catalog.refetch()}
      />
    )
  if (!catalog.data) return <Skeleton lines={10} />
  return (
    <ScenarioWorkspace
      key={catalog.data.artifact_version}
      catalog={catalog.data}
      onReload={() => void catalog.refetch()}
    />
  )
}

interface ScenarioWorkspaceProps {
  readonly catalog: ScenarioCatalog
  readonly onReload: () => void
}

function ScenarioWorkspace({ catalog, onReload }: ScenarioWorkspaceProps) {
  const { t } = useTranslation()
  const errorText = useErrorText()
  const state = useScenarioLab(catalog)
  const result = state.evaluation.data
  const staleVersion =
    isApiError(state.evaluation.error) && state.evaluation.error.code === "stale_scenario_version"
  return (
    <div className={styles.lab}>
      <Banner tone="info" title={t("scenario:method")} description={t("scenario:methodDetail")} />
      <div className={styles.workspace}>
        <Card title={t("scenario:form")} description={t("scenario:formHint")}>
          <Segmented
            label={t("scenario:season")}
            value={state.season}
            onChange={state.setSeason}
            options={[
              { value: "road", label: t("scenario:seasons.road"), icon: "route" },
              { value: "summer", label: t("scenario:seasons.summer"), icon: "sun" },
              { value: "winter", label: t("scenario:seasons.winter"), icon: "snowflake" },
            ]}
          />
          <LinkBuilder
            cities={catalog.cities}
            links={state.links}
            onAdd={state.add}
            onRemove={state.remove}
          />
          <div className={styles.actions}>
            <Button
              icon="refresh"
              pending={state.evaluation.isPending}
              disabled={!state.valid}
              onClick={state.calculate}
            >
              {t("scenario:calculate")}
            </Button>
            <Button variant="secondary" icon="retry" onClick={state.reset}>
              {t("scenario:reset")}
            </Button>
          </div>
        </Card>
        <div className={styles.results} aria-busy={state.evaluation.isPending}>
          {state.stale && (
            <Banner
              tone="warning"
              announce
              title={t("scenario:stale")}
              description={t("scenario:staleHint")}
            />
          )}
          {state.evaluation.isError && (
            <ErrorState
              title={t("scenario:errors.title")}
              description={errorText(state.evaluation.error)}
              onRetry={staleVersion ? onReload : state.calculate}
            />
          )}
          {result ? (
            <ImpactResults result={result} labels={state.labels} />
          ) : (
            !state.evaluation.isError && (
              <EmptyState
                title={t("scenario:empty")}
                description={t("scenario:emptyHint")}
                icon="route"
              />
            )
          )}
        </div>
      </div>
    </div>
  )
}
