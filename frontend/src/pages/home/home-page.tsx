import { MapExplorer } from "@/features/map-explorer"
import { useDocumentTitle } from "@/shared/i18n"

export function HomePage() {
  useDocumentTitle(null)
  return <MapExplorer />
}
