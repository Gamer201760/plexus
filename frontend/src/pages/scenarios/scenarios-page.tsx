import { ScenarioLab } from "@/features/scenario-lab"
import { useDocumentTitle, useTranslation } from "@/shared/i18n"
import { PageHeader } from "@/shared/ui"
import styles from "./scenarios-page.module.css"

export function ScenariosPage() {
  const { t } = useTranslation()
  useDocumentTitle(t("nav:scenarios"))
  return (
    <div className={styles.page}>
      <PageHeader title={t("scenario:title")} description={t("scenario:lead")} />
      <ScenarioLab />
    </div>
  )
}
