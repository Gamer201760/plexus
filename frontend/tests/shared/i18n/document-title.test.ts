import { describe, expect, it } from "vitest"
import { documentTitle, TITLE_SEPARATOR } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/common.json"

describe("documentTitle", () => {
  it("puts the page first and the product second", () => {
    expect(documentTitle("Acme", "Fast checks", "Orders")).toBe("Orders | Acme")
  })

  it("names the home page by the product and its tagline", () => {
    expect(documentTitle("Acme", "Fast checks", null)).toBe("Acme | Fast checks")
    expect(documentTitle("Acme", "", null)).toBe("Acme")
  })

  it("keeps the home title short enough for a tab and a search result", () => {
    const title = documentTitle(ru.app.name, ru.app.tagline, null)
    expect(title).toContain(TITLE_SEPARATOR)
    expect([...title].length).toBeLessThanOrEqual(60)
    expect([...ru.app.name].length).toBeLessThanOrEqual(24)
  })
})
