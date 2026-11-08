import { useIndexStatus } from "@/entities/reference"
import { useDocumentTitle, useTranslation } from "@/shared/i18n"
import { Card, ErrorState, PageHeader, Skeleton, Stat, StatusBadge } from "@/shared/ui"
import { Isolines } from "@/shared/ui/brand"
import { formulaParts } from "./formula-text"
import styles from "./method-page.module.css"

export function MethodPage() {
  const { t } = useTranslation()
  useDocumentTitle(t("method:title"))
  const index = useIndexStatus()
  if (index.isError) {
    return (
      <div className={styles.page}>
        <PageHeader title={t("method:title")} description={t("method:lead")} />
        <ErrorState title={t("errors:kind.server")} onRetry={() => void index.refetch()} />
      </div>
    )
  }
  const data = index.data
  return (
    <div className={styles.page}>
      <PageHeader title={t("method:title")} description={t("method:lead")} />
      {data ? (
        <>
          <section className={styles.formula} aria-label={t("method:formula")}>
            <Isolines rings={3} shape="blob" seed={2} motion="enter" className={styles.rings} />
            <div className={styles.formulaBody}>
              <StatusBadge
                tone={data.status === "ready" ? "success" : "info"}
                label={t(`method:status.${data.status}`)}
              />
              <p className={styles.expression}>{formulaParts(data.formula)}</p>
              <div className={styles.params}>
                <Stat
                  label={t("method:halfLife")}
                  value={t("method:halfLifeValue", { value: data.half_life_hours })}
                />
                <Stat label={t("method:markets")} value={String(data.markets)} />
              </div>
              {data.status === "missing" ? (
                <p className={styles.reason}>{t("map:index.missingText")}</p>
              ) : null}
            </div>
          </section>
          <Card as="section" title={t("method:components")}>
            <dl className={styles.components}>
              {data.components.map((item) => (
                <div key={item.key} className={styles.component}>
                  <dt>{formulaParts(item.title)}</dt>
                  <dd>{item.description}</dd>
                  <dd className={styles.source}>{item.source}</dd>
                </div>
              ))}
            </dl>
          </Card>
        </>
      ) : (
        <Skeleton lines={10} />
      )}
    </div>
  )
}
