import i18next, { type i18n as I18nInstance } from "i18next"
import { initReactI18next } from "react-i18next"
import { LOCALE } from "./locale"
import { DEFAULT_NAMESPACE, NAMESPACES, resources } from "./resources"

export function createI18n(): I18nInstance {
  const instance = i18next.createInstance()
  void instance.use(initReactI18next).init({
    resources,
    lng: LOCALE,
    fallbackLng: LOCALE,
    supportedLngs: [LOCALE],
    ns: [...NAMESPACES],
    defaultNS: DEFAULT_NAMESPACE,
    initAsync: false,
    interpolation: { escapeValue: false },
    returnNull: false,
  })
  return instance
}

export const i18n = createI18n()
