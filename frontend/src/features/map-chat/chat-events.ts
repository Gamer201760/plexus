import type { ChatStreamEvent } from "@/shared/api/chat-stream"
import type { ChatEntry } from "./use-map-chat"

export function applyChatEvent(row: ChatEntry, event: ChatStreamEvent): ChatEntry {
  switch (event.type) {
    case "status":
      return event.code && event.code !== "connecting"
        ? { ...row, steps: [...new Set([...row.steps, event.code])] }
        : row
    case "delta":
      return { ...row, content: row.content + (event.text ?? "") }
    case "table": {
      const table = event.table
      return table
        ? { ...row, tables: [...row.tables.filter((item) => item.id !== table.id), table] }
        : row
    }
    case "chart": {
      const chart = event.chart
      return chart
        ? {
            ...row,
            charts: [...row.charts.filter((item) => item.table_id !== chart.table_id), chart],
          }
        : row
    }
    case "map":
      return event.map
        ? {
            ...row,
            mapCommands: [
              ...row.mapCommands.filter(
                (command) => JSON.stringify(command) !== JSON.stringify(event.map),
              ),
              event.map,
            ],
          }
        : row
    case "calculation":
      return event.calculation
        ? {
            ...row,
            calculations: [
              ...(row.calculations ?? []).filter(
                (item) => item.corridor.id !== event.calculation?.corridor.id,
              ),
              event.calculation,
            ],
          }
        : row
    case "analysis":
      return applyAnalysis(row, event)
    case "done":
      return { ...row, complete: true }
    default:
      return row
  }
}

export function updateChatRows(rows: ChatEntry[], id: string, event: ChatStreamEvent): ChatEntry[] {
  return rows.map((row) => (row.id === id ? applyChatEvent(row, event) : row))
}

export function streamStatus(current: string, event: ChatStreamEvent): string {
  if (event.type === "status") return event.code || "connecting"
  if (event.type === "delta") return "writing"
  if (event.type === "done") return "done"
  return current
}

function applyAnalysis(row: ChatEntry, event: ChatStreamEvent): ChatEntry {
  if (!event.analysis) return row
  return {
    ...row,
    analyses: [
      ...(row.analyses ?? []).filter((item) => item.id !== event.analysis?.id),
      event.analysis,
    ],
  }
}
