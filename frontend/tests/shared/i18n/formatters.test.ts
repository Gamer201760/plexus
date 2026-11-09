import { describe, expect, it } from "vitest"
import { createFormatters, INTL_LOCALE } from "@/shared/i18n"

const SPACES = new RegExp(`[${String.fromCodePoint(0xa0, 0x202f)}]`, "g")
const plain = (text: string) => text.replace(SPACES, " ")

describe("formatters", () => {
  it("formats numbers and percents in russian", () => {
    expect(plain(createFormatters().number(1234.5))).toBe("1 234,5")
    expect(plain(createFormatters().percent(0.427, 1))).toBe("42,7 %")
    expect(plain(createFormatters().percent(0.5))).toBe("50 %")
  })

  it("formats money and dates in a fixed time zone", () => {
    expect(plain(createFormatters().money(12.5, "RUB"))).toBe("12,50 ₽")
    const date = Date.UTC(2026, 2, 14, 9, 30)
    const long = new Intl.DateTimeFormat(INTL_LOCALE, { dateStyle: "long", timeZone: "UTC" })
    expect(createFormatters("UTC").date(date)).toBe(long.format(date))
    expect(createFormatters("UTC").time(date)).toBe("09:30")
  })

  it("joins lists with the russian conjunction", () => {
    const list = new Intl.ListFormat(INTL_LOCALE, { style: "long", type: "conjunction" })
    expect(createFormatters().list(["a", "b", "c"])).toBe(list.format(["a", "b", "c"]))
  })
})
