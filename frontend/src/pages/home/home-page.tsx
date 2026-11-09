import { HomeIntro } from "@/features/home-intro"
import { useDocumentTitle } from "@/shared/i18n"
export function HomePage() {
  useDocumentTitle(null)
  return <HomeIntro />
}
