import { AccessibilityMethod } from "@/features/accessibility-method"
import { useDocumentTitle, useTranslation } from "@/shared/i18n"
import { PageHeader } from "@/shared/ui"
import styles from "./method-page.module.css"
export function MethodPage() {
  const { t } = useTranslation()
  useDocumentTitle(t("method:title"))
  return (
    <div className={styles.page}>
      <PageHeader title={t("method:title")} description={t("method:lead")} />
      <AccessibilityMethod />
    </div>
  )
}
