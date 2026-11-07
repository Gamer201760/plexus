import { type Source, useSources } from "@/entities/reference"
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

export function SourcesPage() {
  const { t } = useTranslation()
  const f = useFormatters()
  useDocumentTitle(t("sources:title"))
  const sources = useSources()
  const columns: DataTableColumn<Source>[] = [
    {
      key: "title",
      header: t("sources:title"),
      cell: (source) => (
        <span className={styles.title}>
          <span>{source.title}</span>
          {source.note ? <span className={styles.note}>{source.note}</span> : null}
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
    {
      key: "url",
      header: t("sources:open"),
      cell: (source) =>
        source.url ? (
          <ButtonLink to={source.url} variant="ghost" size="compact" icon="external">
            {t("sources:open")}
          </ButtonLink>
        ) : (
          <NoValue />
        ),
    },
  ]
  return (
    <div className={styles.page}>
      <PageHeader title={t("sources:title")} description={t("sources:lead")} />
      {sources.isError ? (
        <ErrorState title={t("errors:kind.server")} onRetry={() => void sources.refetch()} />
      ) : sources.data ? (
        <DataTable
          caption={t("sources:title")}
          columns={columns}
          rows={sources.data}
          rowKey={(source) => source.id}
        />
      ) : (
        <Skeleton lines={8} />
      )}
    </div>
  )
}
