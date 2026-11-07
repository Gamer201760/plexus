import { RegionTable } from "@/features/region-table"
import { useDocumentTitle, useTranslation } from "@/shared/i18n"
import { PageHeader } from "@/shared/ui"
import styles from "./regions-page.module.css"

export function RegionsPage() {
  const { t } = useTranslation()
  useDocumentTitle(t("nav:regions"))
  return (
    <div className={styles.page}>
      <PageHeader title={t("nav:regions")} description={t("map:lead")} />
      <RegionTable />
    </div>
  )
}
