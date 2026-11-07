import type { Locale } from "./locale"
import ruCommon from "./locales/ru/common.json"
import ruData from "./locales/ru/data.json"
import ruErrors from "./locales/ru/errors.json"
import ruHealth from "./locales/ru/health.json"
import ruMap from "./locales/ru/map.json"
import ruMethod from "./locales/ru/method.json"
import ruNav from "./locales/ru/nav.json"
import ruRegion from "./locales/ru/region.json"
import ruSeasons from "./locales/ru/seasons.json"
import ruSources from "./locales/ru/sources.json"

export const NAMESPACES = [
  "common",
  "errors",
  "data",
  "health",
  "map",
  "method",
  "nav",
  "region",
  "seasons",
  "sources",
] as const

export type Namespace = (typeof NAMESPACES)[number]

export const DEFAULT_NAMESPACE: Namespace = "common"

const ru = {
  common: ruCommon,
  errors: ruErrors,
  data: ruData,
  health: ruHealth,
  map: ruMap,
  method: ruMethod,
  nav: ruNav,
  region: ruRegion,
  seasons: ruSeasons,
  sources: ruSources,
}

export type Dictionary = typeof ru

export const resources = { ru } satisfies Record<Locale, Record<Namespace, object>>
