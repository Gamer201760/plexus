import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import {
  createI18n,
  LocaleProvider,
  useDocumentTitle,
  useLocale,
  useTranslation,
} from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/common.json"

function Probe({ page }: { readonly page: string | null }) {
  const { t } = useTranslation()
  useDocumentTitle(page)
  const { locale } = useLocale()
  return (
    <button type="button" data-locale={locale}>
      {t("common:action.retry")}
    </button>
  )
}

function renderProbe(page: string | null = null) {
  return render(
    <LocaleProvider instance={createI18n()}>
      <Probe page={page} />
    </LocaleProvider>,
  )
}

describe("LocaleProvider", () => {
  it("renders russian and sets the document language and title", () => {
    renderProbe()
    expect(screen.getByRole("button").textContent).toBe(ru.action.retry)
    expect(screen.getByRole("button").dataset.locale).toBe("ru")
    expect(document.documentElement.lang).toBe("ru")
    expect(document.title).toBe(`${ru.app.name} | ${ru.app.tagline}`)
  })

  it("puts the page title into the tab title", () => {
    renderProbe("Orders")
    expect(document.title).toBe(`Orders | ${ru.app.name}`)
  })

  it("ignores the browser language", () => {
    Object.defineProperty(navigator, "languages", { value: ["en-US"], configurable: true })
    renderProbe()
    expect(screen.getByRole("button").textContent).toBe(ru.action.retry)
  })
})
