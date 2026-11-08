import { Outlet, ScrollRestoration, useLocation } from "react-router"
import { GlobalSearch } from "@/features/global-search"
import { useTranslation } from "@/shared/i18n"
import { AppHeader } from "../app-header/app-header"
import styles from "./root-layout.module.css"
import { useRouteFocus } from "./use-route-focus"

export function RootLayout() {
  const { t } = useTranslation()
  const landing = useLocation().pathname === "/"
  useRouteFocus()
  return (
    <div className={styles.shell}>
      <a className={styles.skip} href="#main">
        {t("common:shell.skip")}
      </a>
      {landing ? null : <AppHeader search={<GlobalSearch />} />}
      <main id="main" tabIndex={-1} className={styles.main}>
        <Outlet />
      </main>
      <ScrollRestoration />
    </div>
  )
}
