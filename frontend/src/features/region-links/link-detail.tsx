import type { Link } from "@/entities/link"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { ButtonLink, Icon, NoValue, Sheet, StatusBadge, type StatusTone } from "@/shared/ui"
import { TransportIcon } from "@/shared/ui/brand"
import styles from "./region-links.module.css"
import { formatSourceDate } from "./source-date"

const CONFIDENCE_TONE: Record<"high" | "medium" | "low", StatusTone> = {
  high: "success",
  medium: "info",
  low: "warning",
}

export interface LinkDetailProps {
  readonly link: Link | null
  readonly onClose: () => void
}

export function LinkDetail({ link, onClose }: LinkDetailProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  if (!link) return <Sheet open={false} onClose={onClose} title={t("region:link.title")} />
  const freq =
    link.freq_per_week === null ? null : t("data:frequency.value", { value: link.freq_per_week })
  return (
    <Sheet
      open
      onClose={onClose}
      placement="responsive"
      title={t(`data:mode.${link.mode}`)}
      actions={
        link.source_url ? (
          <ButtonLink to={link.source_url} variant="secondary" icon="external">
            {t("data:openSource")}
          </ButtonLink>
        ) : null
      }
    >
      <div className={styles.detail}>
        <p className={styles.routeHead}>
          <TransportIcon mode={link.mode} size="lg" />
          <span>{link.from.name}</span>
          <Icon name="arrow-right" size="sm" label={t("region:link.to")} className={styles.arrow} />
          <span>{link.to.name}</span>
        </p>
        {link.confidence || link.freq_assumed ? (
          <div className={styles.detailHead}>
            {link.confidence ? (
              <StatusBadge
                tone={CONFIDENCE_TONE[link.confidence]}
                label={t(`data:confidence.${link.confidence}`)}
              />
            ) : null}
            {link.freq_assumed ? (
              <StatusBadge tone="warning" label={t("data:frequency.assumed")} />
            ) : null}
          </div>
        ) : null}
        <dl className={styles.facts}>
          <dt>{t("region:link.season")}</dt>
          <dd>{link.season ? t(`data:season.${link.season}`) : t("data:season.unknown")}</dd>
          <dt>{t("region:link.distance")}</dt>
          <dd>{link.km === null ? <NoValue /> : `${f.integer(link.km)} ${t("data:unit.km")}`}</dd>
          <dt>{t("region:link.frequency")}</dt>
          <dd>{freq ?? <NoValue />}</dd>
          <dt>{t("region:link.vehicle")}</dt>
          <dd>{link.vehicle ?? <NoValue />}</dd>
          <dt>{t("data:source")}</dt>
          <dd>
            {link.source_date ? (
              t("data:sourceDate", { date: formatSourceDate(link.source_date) })
            ) : (
              <NoValue />
            )}
          </dd>
        </dl>
        {link.freq_note ? (
          <section className={styles.note} lang="ru">
            <p className={styles.noteLabel}>{t("region:link.note")}</p>
            <p>{link.freq_note}</p>
          </section>
        ) : null}
      </div>
    </Sheet>
  )
}
