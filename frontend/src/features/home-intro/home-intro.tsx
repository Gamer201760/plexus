import { useRef } from "react"
import { useSeason } from "@/shared/hooks/use-season"
import { useTranslation } from "@/shared/i18n"
import { usePageVisibility } from "@/shared/motion/use-page-visibility"
import { Button, ButtonLink } from "@/shared/ui"
import { HeroWordmark } from "@/shared/ui/brand/hero-wordmark/hero-wordmark"
import { NetworkScene } from "@/shared/ui/brand/network-scene/network-scene"
import styles from "./home-intro.module.css"

export function HomeIntro() {
  const { t } = useTranslation()
  const { seasonHref } = useSeason()
  const ref = useRef<HTMLDivElement>(null)
  const hidden = usePageVisibility()
  const replay = () =>
    ref.current
      ?.getAnimations({ subtree: true })
      .filter((a) => a.effect?.getTiming().iterations !== Infinity)
      .forEach((a) => {
        a.currentTime = 0
        a.play()
      })
  return (
    <div ref={ref} className={styles.home} data-hidden={hidden}>
      <div className={styles.intro}>
        <HeroWordmark />
        <h1 tabIndex={-1}>
          {t("home:title")}
          <br />
          {t("home:continuation")}
        </h1>
        <ButtonLink to={seasonHref("/map")} icon="map" className={styles.action}>
          {t("home:open")}
        </ButtonLink>
      </div>
      <NetworkScene hidden={hidden} />
      <Button variant="ghost" icon="retry" onClick={replay} className={styles.replay}>
        {t("home:replay")}
      </Button>
    </div>
  )
}
