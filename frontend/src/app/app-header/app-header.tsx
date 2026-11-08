import type { ReactNode } from "react"
import { Link, NavLink } from "react-router"
import { useTranslation } from "@/shared/i18n"
import { Icon, type IconName } from "@/shared/ui"
import { BrandMark } from "@/shared/ui/brand"
import styles from "./app-header.module.css"

interface NavItem {
  readonly to: string
  readonly icon: IconName
  readonly label: "nav:map" | "nav:regions" | "nav:seasons" | "nav:method" | "nav:sources"
}

const NAV: readonly NavItem[] = [
  { to: "/", icon: "map", label: "nav:map" },
  { to: "/regions", icon: "list", label: "nav:regions" },
  { to: "/seasons", icon: "calendar", label: "nav:seasons" },
  { to: "/method", icon: "book", label: "nav:method" },
  { to: "/sources", icon: "database", label: "nav:sources" },
]

export interface AppHeaderProps {
  readonly search?: ReactNode
}

export function AppHeader({ search }: AppHeaderProps) {
  const { t } = useTranslation()
  return (
    <header className={styles.header}>
      <Link to="/" viewTransition className={styles.brand} aria-label={t("common:app.name")}>
        <BrandMark size="fill" rings={2} motion="enter" decorative />
      </Link>
      <nav className={styles.nav} aria-label={t("nav:label")}>
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            viewTransition
            aria-label={t(item.label)}
            className={({ isActive }) =>
              isActive ? `${styles.link} ${styles.active}` : styles.link
            }
          >
            <Icon name={item.icon} size="sm" />
            <span className={styles.label} aria-hidden="true">
              {t(item.label)}
            </span>
          </NavLink>
        ))}
      </nav>
      {search ? <div className={styles.search}>{search}</div> : null}
    </header>
  )
}
