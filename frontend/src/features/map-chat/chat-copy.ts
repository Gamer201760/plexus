import type { MessageKey } from "@/shared/i18n"

const ERRORS: Readonly<Record<string, MessageKey>> = {
  chat_unavailable: "chat:errors.unavailable",
  chat_auth_required: "chat:errors.auth",
  chat_timeout: "chat:errors.timeout",
  chat_limit: "chat:errors.limit",
  chat_busy: "chat:errors.busy",
  chat_local_only: "chat:errors.local",
  chat_connection_error: "chat:errors.connection",
  chat_stream_error: "chat:errors.stream",
}
const STATUSES: Readonly<Record<string, MessageKey>> = {
  idle: "chat:status.idle",
  connecting: "chat:status.connecting",
  writing: "chat:status.writing",
  done: "chat:status.done",
  stopped: "chat:status.stopped",
  error: "chat:status.error",
  compare_regions: "chat:status.comparison",
  calculation_capabilities: "chat:status.calculations",
  accessibility_sensitivity: "chat:status.sensitivity",
  read_road_graph: "chat:status.graph",
  recalculate_road_index: "chat:status.routes",
  control_map: "chat:status.map",
  show_chart: "chat:status.chart",
  list_regions: "chat:status.regions",
  region_links: "chat:status.links",
  region_settlements: "chat:status.settlements",
  search_places: "chat:status.search",
  sources: "chat:status.sources",
}

export const chatErrorKey = (code: string): MessageKey => ERRORS[code] ?? "chat:errors.provider"
export const chatStatusKey = (code: string): MessageKey =>
  STATUSES[code] ?? "chat:status.connecting"
