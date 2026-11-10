import { useMemo, useState } from "react"
import type { MarketCity } from "@/entities/scenario"
import { useSearch } from "@/entities/settlement"
import { useTranslation } from "@/shared/i18n"
import { Combobox, type ComboboxItem } from "@/shared/ui"

export interface PlaceChoice {
  readonly id: string
  readonly label: string
}

export interface PlacePickerProps {
  readonly label: string
  readonly cities: readonly MarketCity[]
  readonly value: PlaceChoice | null
  readonly exclude?: string | undefined
  readonly onSelect: (choice: PlaceChoice) => void
}

const SUGGESTIONS = 6

export function PlacePicker({ label, cities, value, exclude, onSelect }: PlacePickerProps) {
  const { t } = useTranslation()
  const [query, setQuery] = useState("")
  const search = useSearch(query)
  const cityItems = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase("ru-RU")
    if (needle === "") return []
    return cities
      .filter((city) => city.id !== exclude)
      .filter((city) => city.id.toLocaleLowerCase("ru-RU").includes(needle))
      .slice(0, SUGGESTIONS)
      .map((city) => ({ value: city.id, label: city.id, meta: city.region }))
  }, [cities, exclude, query])
  const settlementItems = (search.data?.settlements ?? [])
    .filter((hit) => hit.id !== exclude)
    .slice(0, SUGGESTIONS)
    .map((hit) => ({ value: hit.id, label: hit.name, meta: hit.region_name }))
  const labels = new Map([
    ...cityItems.map((item) => [item.value, item.label] as const),
    ...settlementItems.map((item) => [item.value, item.label] as const),
  ])
  return (
    <Combobox
      label={label}
      placeholder={value === null ? t("scenario:placePlaceholder") : value.label}
      groups={[
        { key: "cities", label: t("scenario:cities"), items: cityItems },
        { key: "settlements", label: t("scenario:settlements"), items: settlementItems },
      ]}
      onQuery={setQuery}
      onSelect={(item: ComboboxItem) =>
        onSelect({ id: item.value, label: labels.get(item.value) ?? item.value })
      }
      loading={search.isFetching}
      emptyText={t("scenario:noMatches")}
    />
  )
}
