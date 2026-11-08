import { useIndexStatus } from "@/entities/reference"
import { useTranslation } from "@/shared/i18n"
import { Card, ErrorState, Skeleton, StatusBadge } from "@/shared/ui"
import { HansenFormula } from "@/shared/ui/data-display/hansen-formula/hansen-formula"
import styles from "./accessibility-method.module.css"
import { ContributionMatrix } from "./contribution-matrix"
export function AccessibilityMethod() {
  const { t } = useTranslation()
  const query = useIndexStatus()
  const data = query.data
  if (query.isError)
    return <ErrorState title={t("errors:kind.server")} onRetry={() => void query.refetch()} />
  if (!data) return <Skeleton lines={10} />
  return (
    <div className={styles.workspace}>
      <Card title={t("method:matrixTitle")} description={t("method:matrixLead")}>
        <ContributionMatrix halfLife={data.half_life_hours} />
      </Card>
      <Card title={t("method:model")}>
        <div className={styles.formula}>
          <HansenFormula label={t("method:formulaLabel")} />
        </div>
        <dl className={styles.definitions}>
          <div>
            <dt>{t("method:market")}</dt>
            <dd>{t("method:marketText", { count: data.markets })}</dd>
          </div>
          <div>
            <dt>{t("method:travel")}</dt>
            <dd>{t("method:travelText")}</dd>
          </div>
          <div>
            <dt>{t("method:decayTitle")}</dt>
            <dd>{t("method:decayText", { hours: data.half_life_hours })}</dd>
          </div>
        </dl>
        <StatusBadge
          tone={data.status === "ready" ? "success" : "info"}
          label={t(`method:status.${data.status}`)}
        />
      </Card>
    </div>
  )
}
