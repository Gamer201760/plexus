import { MapExplorer } from "@/features/map-explorer"
import { useDocumentTitle, useTranslation } from "@/shared/i18n"

export function MapPage() {
  const { t } = useTranslation()
  useDocumentTitle(t("nav:map"))
  return (
    <>
      <h1 className="visually-hidden" tabIndex={-1}>
        {t("map:title")}
      </h1>
      <MapExplorer />
    </>
  )
}
