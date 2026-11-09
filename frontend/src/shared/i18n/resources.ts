import type { Locale } from "./locale"
import ruAtlas from "./locales/ru/atlas.json"
import ruCalendar from "./locales/ru/calendar.json"
import ruCommon from "./locales/ru/common.json"
import ruCompare from "./locales/ru/compare.json"
import ruData from "./locales/ru/data.json"
import ruErrors from "./locales/ru/errors.json"
import ruHealth from "./locales/ru/health.json"
import ruLinks from "./locales/ru/links.json"
import ruMap from "./locales/ru/map.json"
import ruNav from "./locales/ru/nav.json"
import ruPilot from "./locales/ru/pilot.json"
import ruProfile from "./locales/ru/profile.json"
import ruRegion from "./locales/ru/region.json"
import ruSeasons from "./locales/ru/seasons.json"
import ruSources from "./locales/ru/sources.json"

export const NAMESPACES = [
  "common",
  "errors",
  "atlas",
  "calendar",
  "compare",
  "data",
  "health",
  "links",
  "map",
  "nav",
  "pilot",
  "profile",
  "region",
  "seasons",
  "sources",
] as const

export type Namespace = (typeof NAMESPACES)[number]

export const DEFAULT_NAMESPACE: Namespace = "common"

const ru = {
  common: ruCommon,
  errors: ruErrors,
  atlas: ruAtlas,
  calendar: ruCalendar,
  compare: ruCompare,
  data: ruData,
  health: ruHealth,
  links: ruLinks,
  map: ruMap,
  nav: ruNav,
  pilot: ruPilot,
  profile: ruProfile,
  region: ruRegion,
  seasons: ruSeasons,
  sources: ruSources,
}

export type Dictionary = typeof ru

export const resources = { ru } satisfies Record<Locale, Record<Namespace, object>>
