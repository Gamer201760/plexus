import { usePilot } from "@/entities/pilot"
import { PilotExperiment } from "@/features/pilot-experiment"
import { useDocumentTitle, useErrorText, useTranslation } from "@/shared/i18n"
import { ErrorState, PageHeader, Skeleton } from "@/shared/ui"
import styles from "./pilot-page.module.css"

export function PilotPage() {
  const { t } = useTranslation()
  useDocumentTitle(t("pilot:title"))
  const query = usePilot("tuva")
  const errorText = useErrorText()
  return (
    <div className={styles.page}>
      <PageHeader title={t("pilot:title")} description={t("pilot:lead")} />
      {query.data ? (
        <PilotExperiment
          key={query.data.artifact_version}
          pilot={query.data}
          onReload={() => query.refetch().then((result) => !result.isError)}
        />
      ) : query.isError ? (
        <ErrorState title={errorText(query.error)} onRetry={() => void query.refetch()} />
      ) : (
        <Skeleton lines={12} />
      )}
    </div>
  )
}
