import { MapExplorer } from "@/features/map-explorer"
import { useDocumentTitle, useTranslation } from "@/shared/i18n"

export function HomePage() {
  const { t } = useTranslation()
  useDocumentTitle(null)
  return (
    <>
      <h1 className="visually-hidden" tabIndex={-1}>
        {t("map:title")}
      </h1>
      <MapExplorer />
    </>
  )
}
