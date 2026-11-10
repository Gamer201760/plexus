import { useTranslation } from "@/shared/i18n"
import { ButtonLink, Icon, StatusBadge } from "@/shared/ui"
import { TransportIcon } from "@/shared/ui/brand"
import type { Link } from "../link.queries"
import styles from "./link-list.module.css"

export interface LinkListProps {
  readonly rows: readonly Link[]
}
export function LinkList({ rows }: LinkListProps) {
  const { t } = useTranslation()
  return (
    <ul className={styles.list}>
      {rows.map((link) => (
        <li key={link.id} data-link-id={link.id}>
          <TransportIcon mode={link.mode} size="sm" />
          <div className={styles.content}>
            <div className={styles.route}>
              <span>{link.from.name}</span>
              <Icon name="arrow-right" size="sm" />
              <span>{link.to.name}</span>
            </div>
            <div className={styles.metadata}>
              {link.is_model ? <StatusBadge tone="info" label={t("data:modelLink.badge")} /> : null}
              <span>{t(`data:mode.${link.mode}`)}</span>
              <span>{t(`data:season.${link.season ?? "unknown"}`)}</span>
            </div>
          </div>
          {link.source_url ? (
            <ButtonLink to={link.source_url} icon="external" variant="ghost">
              <span className="visually-hidden">{t("data:openSource")}</span>
            </ButtonLink>
          ) : null}
        </li>
      ))}
    </ul>
  )
}
