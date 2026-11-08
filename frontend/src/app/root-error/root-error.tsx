import { useEffect } from "react"
import { Link, useRouteError } from "react-router"
import { useDocumentTitle, useTranslation } from "@/shared/i18n"
import { Button, ButtonLink, StatusScreen } from "@/shared/ui"
import { BrandMark, IsoText } from "@/shared/ui/brand"
import styles from "./root-error.module.css"

export function RootError() {
  const { t } = useTranslation()
  const error = useRouteError()
  useDocumentTitle(t("errors:boundary.title"))
  useEffect(() => {
    console.error(error)
  }, [error])
  return (
    <div className={styles.shell}>
      <header className={styles.top}>
        <Link to="/" className={styles.brand} aria-label={t("common:app.name")}>
          <BrandMark size="md" rings={2} decorative />
        </Link>
      </header>
      <main id="main">
        <StatusScreen
          art={<IsoText text={t("errors:boundary.art")} />}
          title={t("errors:boundary.title")}
          description={t("errors:boundary.description")}
          actions={
            <>
              <Button icon="refresh" onClick={() => window.location.reload()}>
                {t("errors:boundary.reload")}
              </Button>
              <ButtonLink to="/" variant="secondary" icon="map">
                {t("errors:boundary.home")}
              </ButtonLink>
            </>
          }
        />
      </main>
    </div>
  )
}
