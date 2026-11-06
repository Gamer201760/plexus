import type { Locale } from "./locale"
import enCommon from "./locales/en/common.json"
import enErrors from "./locales/en/errors.json"
import enHealth from "./locales/en/health.json"
import enHome from "./locales/en/home.json"
import ruCommon from "./locales/ru/common.json"
import ruErrors from "./locales/ru/errors.json"
import ruHealth from "./locales/ru/health.json"
import ruHome from "./locales/ru/home.json"

export const NAMESPACES = ["common", "errors", "health", "home"] as const

export type Namespace = (typeof NAMESPACES)[number]

export const DEFAULT_NAMESPACE: Namespace = "common"

const en = {
  common: enCommon,
  errors: enErrors,
  health: enHealth,
  home: enHome,
}

const ru = {
  common: ruCommon,
  errors: ruErrors,
  health: ruHealth,
  home: ruHome,
}

export type Dictionary = typeof en

export const resources = { en, ru } satisfies Record<Locale, Record<Namespace, object>>
