import type { ChatEntry } from "./use-map-chat"

export function historyContent(row: ChatEntry): string {
  if (!row.tables.length && !row.mapCommands.length && !row.calculations?.length)
    return row.content.slice(0, 12000)
  const context = {
    displayed_tables: row.tables.map((table) => ({
      title: table.title,
      rows: table.rows.map(({ id, name, origin, destination }) => ({
        id,
        name,
        origin,
        destination,
      })),
    })),
    map_commands: row.mapCommands,
    calculations: row.calculations?.map((item) => ({
      corridor_id: item.corridor.id,
      job_ids: item.job_ids,
    })),
  }
  return `${row.content.slice(0, 6000)}\n\nDisplayed data context:\n${JSON.stringify(context)}`.slice(
    0,
    12000,
  )
}
