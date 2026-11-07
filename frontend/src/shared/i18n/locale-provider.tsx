import type { i18n as I18nInstance } from "i18next"
import { createContext, type ReactNode, useEffect, useMemo, useState } from "react"
import { I18nextProvider } from "react-i18next"
import { documentTitle } from "./document-title"
import { i18n as defaultInstance } from "./instance"
import { LOCALE, type Locale } from "./locale"
import { NAMESPACES } from "./resources"

export interface LocaleState {
  readonly locale: Locale
  readonly setPageTitle: (title: string | null) => void
}

export const LocaleContext = createContext<LocaleState | null>(null)

export interface LocaleProviderProps {
  readonly children: ReactNode
  readonly instance?: I18nInstance
}

export function LocaleProvider({ children, instance = defaultInstance }: LocaleProviderProps) {
  const [pageTitle, setPageTitle] = useState<string | null>(null)

  useEffect(() => {
    document.documentElement.lang = LOCALE
    const t = instance.getFixedT(LOCALE, NAMESPACES)
    document.title = documentTitle(t("common:app.name"), t("common:app.tagline"), pageTitle)
  }, [instance, pageTitle])

  const value = useMemo(() => ({ locale: LOCALE, setPageTitle }), [])

  return (
    <I18nextProvider i18n={instance}>
      <LocaleContext value={value}>{children}</LocaleContext>
    </I18nextProvider>
  )
}
