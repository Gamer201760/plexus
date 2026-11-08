import { SeasonSummary } from "@/entities/region"
import { MapExplorer } from "@/features/map-explorer"
import { useDocumentTitle, useTranslation } from "@/shared/i18n"
import { PageHeader } from "@/shared/ui"
import styles from "./map-page.module.css"
export function MapPage() {
  const { t } = useTranslation()
  useDocumentTitle(t("nav:map"))
  return (
    <div className={styles.page}>
      <PageHeader title={t("atlas:mapTitle")} description={t("atlas:mapLead")} />
      <SeasonSummary />
      <MapExplorer />
    </div>
  )
}
