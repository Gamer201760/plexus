import { useSearchParams } from "react-router"
import { useSources } from "@/entities/reference"
import { useFormatters, useTranslation } from "@/shared/i18n"
import {
  ButtonLink,
  Card,
  Disclosure,
  EmptyState,
  ErrorState,
  NoValue,
  Skeleton,
  Tabs,
} from "@/shared/ui"
import styles from "./source-catalog.module.css"
import { sourceTopic, sourceUsage, TOPIC_ICONS, TOPICS } from "./source-topics"

let rememberedTopic = "network"

export function SourceCatalog() {
  const { t } = useTranslation()
  const f = useFormatters()
  const sources = useSources()
  const [params, setParams] = useSearchParams()
  const topic = TOPICS.find((key) => key === (params.get("topic") ?? rememberedTopic)) ?? "network"
  const entries = sources.data?.filter((source) => sourceTopic(source.id) === topic)
  return (
    <Tabs
      label={t("sources:topicsLabel")}
      items={TOPICS.map((value) => ({
        value,
        label: t(`sources:topics.${value}`),
        icon: TOPIC_ICONS[value],
      }))}
      value={topic}
      onChange={(next) => {
        rememberedTopic = next
        setParams(
          (current) => {
            const p = new URLSearchParams(current)
            p.set("topic", next)
            return p
          },
          { replace: true, preventScrollReset: true },
        )
      }}
    >
      {sources.isError ? (
        <ErrorState title={t("errors:kind.server")} onRetry={() => void sources.refetch()} />
      ) : !sources.data ? (
        <Skeleton lines={8} />
      ) : (
        <div className={styles.catalog}>
          {entries?.map((s) => (
            <Card
              as="article"
              key={s.id}
              className={styles.entry}
              title={s.title}
              description={
                s.note ?? (s.id === "region-geometry" ? t("sources:geometry") : undefined)
              }
              actions={
                <div className={styles.actions}>
                  <dl className={styles.metadata}>
                    <div>
                      <dt>{t("sources:period")}</dt>
                      <dd>{s.period ?? <NoValue />}</dd>
                    </div>
                    <div>
                      <dt>{t("sources:rows")}</dt>
                      <dd>{s.rows === null ? <NoValue /> : f.integer(s.rows)}</dd>
                    </div>
                  </dl>
                  {s.url ? (
                    <ButtonLink to={s.url} variant="ghost" icon="external">
                      <span className="visually-hidden">
                        {t("sources:openNamed", { title: s.title })}
                      </span>
                    </ButtonLink>
                  ) : (
                    <span className={styles.noLink}>{t("sources:inside")}</span>
                  )}
                </div>
              }
            >
              <div className={styles.usage}>
                <Disclosure title={t("sources:usage")}>
                  <p>{t(`sources:uses.${sourceUsage(s.id)}`)}</p>
                </Disclosure>
              </div>
            </Card>
          ))}
          {entries?.length === 0 ? <EmptyState icon="database" title={t("sources:empty")} /> : null}
        </div>
      )}
    </Tabs>
  )
}
