import { INTL_LOCALE } from "@/shared/i18n"

const PARTIAL_DATE = /^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?$/
const monthYear = new Intl.DateTimeFormat(INTL_LOCALE, { month: "long", year: "numeric" })
const fullDate = new Intl.DateTimeFormat(INTL_LOCALE, { dateStyle: "long" })
const yearOnly = new Intl.DateTimeFormat(INTL_LOCALE, { year: "numeric" })

export function formatSourceDate(value: string) {
  const match = PARTIAL_DATE.exec(value)
  if (!match) return value
  const [, year, month, day] = match
  const date = new Date(Number(year), month ? Number(month) - 1 : 0, day ? Number(day) : 1)
  if (day) return fullDate.format(date)
  if (month) return monthYear.format(date)
  return yearOnly.format(date)
}
