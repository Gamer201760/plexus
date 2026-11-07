import { Link } from "react-router"
import { useTranslation } from "@/shared/i18n"
import styles from "./app-header.module.css"

export function AppHeader() {
  const { t } = useTranslation()
  return (
    <header className={styles.header}>
      <Link to="/" viewTransition className={styles.brand}>
        {t("common:app.name")}
      </Link>
    </header>
  )
}
