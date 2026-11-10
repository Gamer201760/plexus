import type { ChatChart, ChatTable as Table } from "@/shared/api/chat-artifacts"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { BarChart, Card, Disclosure } from "@/shared/ui"
import styles from "./chat-artifacts.module.css"
import { ChatTable, columnKey, formatCell } from "./chat-table"

export interface ChatArtifactsProps {
  readonly tables: readonly Table[]
  readonly charts: readonly ChatChart[]
}

export function ChatArtifacts({ tables, charts }: ChatArtifactsProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  if (!tables.length) return null
  return (
    <div className={styles.blocks}>
      {tables.map((table) => {
        const chart = charts.find((item) => item.table_id === table.id)
        const y = table.columns.find((column) => column.key === chart?.y)
        const title = chart && y ? t(columnKey(y.key)) : t(`chat:tables.${table.title}`)
        return (
          <Card as="div" key={table.id} title={title} className={styles.block}>
            {chart && y ? (
              <>
                <BarChart
                  label={title}
                  items={table.rows.map((row) => {
                    const value = row[chart.y]
                    return {
                      key: String(row.id),
                      label: String(row[chart.x] ?? ""),
                      value: typeof value === "number" ? value : null,
                      display: value == null ? t("chat:missing") : formatCell(y, value, f),
                    }
                  })}
                />
                <Disclosure title={t("chat:tableData")}>
                  <ChatTable table={table} />
                </Disclosure>
              </>
            ) : (
              <ChatTable table={table} />
            )}
            <a className={styles.source} href={table.source} target="_blank" rel="noreferrer">
              {t("chat:tableSource")}
            </a>
          </Card>
        )
      })}
    </div>
  )
}
