import { RegionCompare } from "@/features/region-compare"
import { useDocumentTitle, useTranslation } from "@/shared/i18n"
import { PageHeader } from "@/shared/ui"
import styles from "./compare-page.module.css"

export function ComparePage() {
  const { t } = useTranslation()
  useDocumentTitle(t("nav:compare"))
  return (
    <div className={styles.page}>
      <PageHeader title={t("compare:title")} description={t("compare:lead")} />
      <RegionCompare />
    </div>
  )
}
