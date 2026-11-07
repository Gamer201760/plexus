import type { Locale } from "./locale"
import ruCommon from "./locales/ru/common.json"
import ruErrors from "./locales/ru/errors.json"
import ruHealth from "./locales/ru/health.json"
import ruHome from "./locales/ru/home.json"

export const NAMESPACES = ["common", "errors", "health", "home"] as const

export type Namespace = (typeof NAMESPACES)[number]

export const DEFAULT_NAMESPACE: Namespace = "common"

const ru = {
  common: ruCommon,
  errors: ruErrors,
  health: ruHealth,
  home: ruHome,
}

export type Dictionary = typeof ru

export const resources = { ru } satisfies Record<Locale, Record<Namespace, object>>
