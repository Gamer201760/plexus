import type { components } from "./schema.gen"

export type ChatTable = components["schemas"]["ChatTable"]
export type ChatChart = components["schemas"]["ChatChart"]
export type ChatColumn = components["schemas"]["ChatColumn"]
export type ChatRow = ChatTable["rows"][number]

export function isChatTable(value: unknown): value is ChatTable {
  if (typeof value !== "object" || value === null) return false
  if (
    !("id" in value) ||
    typeof value.id !== "string" ||
    !("title" in value) ||
    !["regions", "links", "settlements", "sensitivity"].includes(String(value.title))
  )
    return false
  if (
    !("columns" in value) ||
    !Array.isArray(value.columns) ||
    !("rows" in value) ||
    !Array.isArray(value.rows)
  )
    return false
  return (
    value.columns.every(
      (column: unknown) =>
        typeof column === "object" &&
        column !== null &&
        "key" in column &&
        typeof column.key === "string" &&
        "format" in column &&
        ["text", "number", "integer", "percent"].includes(String(column.format)),
    ) &&
    value.rows.every(
      (row: unknown) =>
        typeof row === "object" &&
        row !== null &&
        Object.values(row).every(
          (cell: unknown) =>
            cell === null ||
            typeof cell === "string" ||
            (typeof cell === "number" && Number.isFinite(cell)),
        ),
    ) &&
    "total" in value &&
    typeof value.total === "number" &&
    "source" in value &&
    typeof value.source === "string" &&
    "truncated" in value &&
    typeof value.truncated === "boolean"
  )
}

export function isChatChart(value: unknown): value is ChatChart {
  return (
    typeof value === "object" &&
    value !== null &&
    "table_id" in value &&
    typeof value.table_id === "string" &&
    "x" in value &&
    typeof value.x === "string" &&
    "y" in value &&
    typeof value.y === "string" &&
    "type" in value &&
    value.type === "bar"
  )
}
