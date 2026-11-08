import { useTranslation } from "@/shared/i18n"
import { usePageVisibility } from "@/shared/motion/use-page-visibility"
import { ButtonLink } from "@/shared/ui"
import { HeroWordmark } from "@/shared/ui/brand/hero-wordmark/hero-wordmark"
import { NetworkScene } from "@/shared/ui/brand/network-scene/network-scene"
import styles from "./home-intro.module.css"

export function HomeIntro() {
  const { t } = useTranslation()
  const hidden = usePageVisibility()
  return (
    <div className={styles.home} data-hidden={hidden}>
      <div className={styles.intro}>
        <HeroWordmark />
        <h1 tabIndex={-1}>
          {t("home:title")}
          <br />
          {t("home:continuation")}
        </h1>
        <ButtonLink to="/map" icon="map" className={styles.action}>
          {t("home:open")}
        </ButtonLink>
      </div>
      <NetworkScene hidden={hidden} />
    </div>
  )
}
