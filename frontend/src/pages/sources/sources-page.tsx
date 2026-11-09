import { type Source, useSources } from "@/entities/reference"
import { useMediaQuery } from "@/shared/hooks"
import { useDocumentTitle, useFormatters, useTranslation } from "@/shared/i18n"
import {
  ButtonLink,
  DataTable,
  type DataTableColumn,
  ErrorState,
  NoValue,
  PageHeader,
  Skeleton,
} from "@/shared/ui"
import styles from "./sources-page.module.css"

interface OpenLinkProps {
  readonly source: Source
}

function OpenLink({ source }: OpenLinkProps) {
  const { t } = useTranslation()
  if (!source.url) return null
  return (
    <ButtonLink
      reloadDocument={source.url.startsWith("/datasets/")}
      to={source.url}
      variant="ghost"
      size="compact"
      icon="external"
    >
      <span aria-hidden="true">{t("sources:open")}</span>
      <span className="visually-hidden">{t("sources:openNamed", { title: source.title })}</span>
    </ButtonLink>
  )
}

export function SourcesPage() {
  const { t } = useTranslation()
  const f = useFormatters()
  useDocumentTitle(t("sources:title"))
  const sources = useSources()
  const narrow = useMediaQuery("(max-width: 48rem)")
  const columns: DataTableColumn<Source>[] = [
    {
      key: "title",
      header: t("sources:title"),
      cell: (source) => (
        <span className={styles.title}>
          <span>{source.title}</span>
          {source.note ? <span className={styles.note}>{source.note}</span> : null}
          {narrow ? (
            <span className={styles.inlineLink}>
              <OpenLink source={source} />
            </span>
          ) : null}
        </span>
      ),
    },
    { key: "period", header: t("sources:period"), cell: (source) => source.period ?? <NoValue /> },
    {
      key: "rows",
      header: t("sources:rows"),
      cell: (source) => (source.rows === null ? <NoValue /> : f.integer(source.rows)),
      numeric: true,
      sortable: true,
      sortValue: (source) => source.rows ?? -1,
    },
  ]
  const linkColumn: DataTableColumn<Source> = {
    key: "url",
    header: t("sources:link"),
    cell: (source) => <OpenLink source={source} />,
  }
  return (
    <div className={styles.page} aria-busy={sources.data === undefined}>
      <PageHeader title={t("sources:title")} description={t("sources:lead")} />
      {sources.isError ? (
        <ErrorState title={t("errors:kind.server")} onRetry={() => void sources.refetch()} />
      ) : sources.data ? (
        <DataTable
          caption={t("sources:title")}
          columns={narrow ? columns : [...columns, linkColumn]}
          rows={sources.data}
          rowKey={(source) => source.id}
        />
      ) : (
        <Skeleton lines={8} className={styles.bone} />
      )}
    </div>
  )
}
