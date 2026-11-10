import { useState } from "react"
import type { ChatColumn, ChatRow, ChatTable as Table } from "@/shared/api/chat-artifacts"
import { type Formatters, type MessageKey, useFormatters, useTranslation } from "@/shared/i18n"
import { Button, DataTable } from "@/shared/ui"

const MODES: Readonly<Record<string, MessageKey>> = {
  rail: "data:mode.rail",
  air: "data:mode.air",
  bus: "data:mode.bus",
  river: "data:mode.river",
  winter_road: "data:mode.winter_road",
  ferry: "data:mode.ferry",
  ice_crossing: "data:mode.ice_crossing",
  pontoon_bridge: "data:mode.pontoon_bridge",
}

const LABELS: Readonly<Record<string, MessageKey>> = {
  name: "chat:columns.name",
  time_multiplier: "chat:columns.timeMultiplier",
  delta: "chat:columns.delta",
  relative_change: "chat:columns.relativeChange",
  hansen: "chat:columns.hansen",
  population: "data:metric.population",
  links_season: "data:metric.links",
  settlements: "chat:columns.settlements",
  companies: "data:metric.companies",
  coverage: "data:network.coverageColumn",
  origin: "chat:columns.origin",
  destination: "chat:columns.destination",
  mode: "chat:columns.mode",
  frequency: "chat:columns.frequency",
}

export const columnKey = (key: string): MessageKey => LABELS[key] ?? "chat:columns.value"

export function formatCell(column: ChatColumn, value: ChatRow[string], f: Formatters): string {
  if (value === null || value === undefined) return ""
  if (typeof value !== "number") return value
  if (column.format === "percent") return f.percent(value, 1)
  return column.format === "integer" ? f.integer(value) : f.number(value, 3)
}

export function ChatTable({ table }: { readonly table: Table }) {
  const { t } = useTranslation()
  const f = useFormatters()
  const [expanded, setExpanded] = useState(false)
  const rows = expanded ? table.rows : table.rows.slice(0, 8)
  const columns = table.columns.map((column) => ({
    key: column.key,
    header: t(columnKey(column.key)),
    numeric: column.format !== "text",
    cell: (row: ChatRow) => {
      const value = row[column.key]
      if (value === null || value === undefined) return t("chat:missing")
      if (column.key === "mode" && value in MODES) return t(MODES[value] ?? "chat:missing")
      return formatCell(column, value, f)
    },
  }))
  return (
    <>
      {table.title === "sensitivity" ? <p>{t("chat:sensitivityNote")}</p> : null}
      <DataTable
        caption={t(`chat:tables.${table.title}`)}
        columns={columns}
        rows={rows}
        rowKey={(row) => String(row.id)}
      />
      {table.rows.length > 8 ? (
        <Button variant="ghost" icon="list" onClick={() => setExpanded(!expanded)}>
          {t(expanded ? "chat:collapse" : "chat:showAll", {
            count: table.rows.length,
          })}
        </Button>
      ) : null}
      {table.truncated ? (
        <p>{t("chat:truncated", { shown: table.rows.length, total: table.total })}</p>
      ) : null}
    </>
  )
}
