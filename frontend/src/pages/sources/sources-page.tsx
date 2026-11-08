import { SourceCatalog } from "@/features/source-catalog"
import { useDocumentTitle, useTranslation } from "@/shared/i18n"
import { PageHeader } from "@/shared/ui"
import styles from "./sources-page.module.css"
export function SourcesPage() {
  const { t } = useTranslation()
  useDocumentTitle(t("sources:title"))
  return (
    <div className={styles.page}>
      <PageHeader title={t("sources:title")} />
      <SourceCatalog />
    </div>
  )
}
