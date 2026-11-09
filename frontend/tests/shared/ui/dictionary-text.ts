import common from "@/shared/i18n/locales/ru/common.json"
import errors from "@/shared/i18n/locales/ru/errors.json"

export const text = {
  title: common.app.tagline,
  description: common.meta.description,
  formats: {
    title: common.app.name,
    number: common.action.retry,
    percent: errors.boundary.title,
    money: common.state.loading,
    date: errors.kind.server,
    count: common.value.noneLabel,
    missing: errors.kind.unknown,
  },
  empty: {
    title: common.notFound.title,
    description: common.notFound.description,
  },
} as const
