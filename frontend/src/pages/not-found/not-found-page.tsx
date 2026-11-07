import { useDocumentTitle, useTranslation } from "@/shared/i18n"
import { ButtonLink } from "@/shared/ui"
import { BrandMark } from "@/shared/ui/brand"
import styles from "./not-found-page.module.css"

export function NotFoundPage() {
  const { t } = useTranslation()
  useDocumentTitle(t("common:notFound.title"))
  return (
    <section className={styles.page}>
      <BrandMark kind="symbol-full" size="xl" motion="enter" broken decorative />
      <div className={styles.copy}>
        <h1 className={styles.title}>{t("common:notFound.title")}</h1>
        <p className={styles.description}>{t("common:notFound.description")}</p>
        <ButtonLink to="/" icon="home">
          {t("common:action.home")}
        </ButtonLink>
      </div>
    </section>
  )
}
