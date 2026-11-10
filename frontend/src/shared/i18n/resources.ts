import type { Locale } from "./locale"
import ruAnalysis from "./locales/ru/analysis.json"
import ruAtlas from "./locales/ru/atlas.json"
import ruCalendar from "./locales/ru/calendar.json"
import ruChat from "./locales/ru/chat.json"
import ruCommon from "./locales/ru/common.json"
import ruCompare from "./locales/ru/compare.json"
import ruData from "./locales/ru/data.json"
import ruErrors from "./locales/ru/errors.json"
import ruGraph from "./locales/ru/graph.json"
import ruHealth from "./locales/ru/health.json"
import ruLinks from "./locales/ru/links.json"
import ruMap from "./locales/ru/map.json"
import ruNav from "./locales/ru/nav.json"
import ruProfile from "./locales/ru/profile.json"
import ruRegion from "./locales/ru/region.json"
import ruScenario from "./locales/ru/scenario.json"
import ruSeasons from "./locales/ru/seasons.json"
import ruSources from "./locales/ru/sources.json"

export const NAMESPACES = [
  "analysis",
  "common",
  "errors",
  "atlas",
  "calendar",
  "chat",
  "compare",
  "data",
  "graph",
  "health",
  "links",
  "map",
  "nav",
  "profile",
  "region",
  "scenario",
  "seasons",
  "sources",
] as const

export type Namespace = (typeof NAMESPACES)[number]

export const DEFAULT_NAMESPACE: Namespace = "common"

const ru = {
  analysis: ruAnalysis,
  common: ruCommon,
  errors: ruErrors,
  atlas: ruAtlas,
  calendar: ruCalendar,
  chat: ruChat,
  compare: ruCompare,
  data: ruData,
  graph: ruGraph,
  health: ruHealth,
  links: ruLinks,
  map: ruMap,
  nav: ruNav,
  profile: ruProfile,
  region: ruRegion,
  scenario: ruScenario,
  seasons: ruSeasons,
  sources: ruSources,
}

export type Dictionary = typeof ru

export const resources = { ru } satisfies Record<Locale, Record<Namespace, object>>
