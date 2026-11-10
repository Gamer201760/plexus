import type { components } from "./schema.gen"

export type ChatMapCommand = components["schemas"]["ChatMapCommand"]
export type MapCommandHandler = (command: ChatMapCommand) => void

export function isChatMapCommand(value: unknown): value is ChatMapCommand {
  if (
    typeof value !== "object" ||
    value === null ||
    !("action" in value) ||
    !("region_ids" in value)
  )
    return false
  if (!["focus", "reset", "zoom_in", "zoom_out"].includes(String(value.action))) return false
  if (
    !Array.isArray(value.region_ids) ||
    !value.region_ids.every((id: unknown) => typeof id === "string" && /^\d{8}$/.test(id))
  )
    return false
  return value.action === "focus"
    ? value.region_ids.length > 0 && value.region_ids.length <= 30
    : value.region_ids.length === 0
}
