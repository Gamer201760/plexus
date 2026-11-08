import { useState } from "react"
import { useNavigate } from "react-router"
import { useSearch } from "@/entities/settlement"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Combobox, type ComboboxGroup } from "@/shared/ui"

const REGION = "region:"
const SETTLEMENT = "settlement:"

export function GlobalSearch() {
  const { t } = useTranslation()
  const f = useFormatters()
  const navigate = useNavigate()
  const [query, setQuery] = useState("")
  const search = useSearch(query)
  const data = search.data
  const groups: ComboboxGroup[] = data
    ? [
        {
          key: "regions",
          label: t("nav:search.regions"),
          items: data.regions.map((region) => ({
            value: `${REGION}${region.id}`,
            label: region.name,
            icon: "map" as const,
          })),
        },
        {
          key: "settlements",
          label: t("nav:search.settlements"),
          items: data.settlements.map((item) => ({
            value: `${SETTLEMENT}${item.region_id}:${item.id}`,
            label: item.name,
            icon: "home" as const,
            meta:
              item.population === null
                ? item.region_name
                : `${item.region_name}, ${f.compact(item.population)}`,
          })),
        },
      ].filter((group) => group.items.length > 0)
    : []
  return (
    <Combobox
      label={t("nav:search.label")}
      hideLabel
      placeholder={t("nav:search.placeholder")}
      groups={groups}
      loading={search.isFetching}
      minLength={2}
      align="end"
      onQuery={setQuery}
      onSelect={(item) => {
        if (item.value.startsWith(REGION)) {
          void navigate(`/regions/${item.value.slice(REGION.length)}`, { viewTransition: true })
          return
        }
        const [regionId, settlementId] = item.value.slice(SETTLEMENT.length).split(":")
        void navigate(`/regions/${regionId}?settlement=${settlementId}`, { viewTransition: true })
      }}
    />
  )
}
