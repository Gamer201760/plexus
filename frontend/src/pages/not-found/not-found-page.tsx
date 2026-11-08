import { useLocation } from "react-router"
import { useDocumentTitle, useTranslation } from "@/shared/i18n"
import { ButtonLink, StatusScreen } from "@/shared/ui"
import { IsoText } from "@/shared/ui/brand"
import styles from "./not-found-page.module.css"

export function NotFoundPage() {
  const { t } = useTranslation()
  const { pathname } = useLocation()
  useDocumentTitle(t("common:notFound.title"))
  return (
    <StatusScreen
      art={<IsoText text="404" />}
      title={t("common:notFound.title")}
      description={t("common:notFound.description")}
      actions={
        <>
          <ButtonLink to="/" icon="map">
            {t("common:action.home")}
          </ButtonLink>
          <ButtonLink to="/regions" variant="secondary" icon="list">
            {t("common:notFound.regions")}
          </ButtonLink>
        </>
      }
    >
      <p className={styles.path}>
        <span>{t("common:notFound.path")}</span>
        <code className={styles.code}>{pathname}</code>
      </p>
    </StatusScreen>
  )
}
