import type { ChatEntry } from "./use-map-chat"

export function historyContent(row: ChatEntry): string {
  if (
    !row.tables.length &&
    !row.mapCommands.length &&
    !row.calculations?.length &&
    !row.analyses?.length
  )
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
    analyses: row.analyses?.map(({ id, region_id, mode }) => ({ id, region_id, mode })),
    commentaries: Object.values(row.commentaries ?? {})
      .filter((value) => value.complete)
      .map((value) => value.text.slice(0, 2000)),
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
