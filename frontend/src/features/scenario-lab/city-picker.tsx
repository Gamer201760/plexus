import { useMemo, useState } from "react"
import type { MarketCity } from "@/entities/scenario"
import { useTranslation } from "@/shared/i18n"
import { Combobox, type ComboboxItem } from "@/shared/ui"

export interface CityPickerProps {
  readonly label: string
  readonly cities: readonly MarketCity[]
  readonly value: string
  readonly exclude?: string | undefined
  readonly onSelect: (id: string) => void
  readonly className?: string | undefined
}

const SUGGESTIONS = 8

export function CityPicker({
  label,
  cities,
  value,
  exclude,
  onSelect,
  className,
}: CityPickerProps) {
  const { t } = useTranslation()
  const [query, setQuery] = useState("")
  const items = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase("ru-RU")
    if (needle === "") return []
    return cities
      .filter((city) => city.id !== exclude)
      .filter((city) => city.id.toLocaleLowerCase("ru-RU").includes(needle))
      .slice(0, SUGGESTIONS)
      .map((city) => ({ value: city.id, label: city.id, meta: city.region }))
  }, [cities, exclude, query])
  return (
    <Combobox
      label={label}
      placeholder={value === "" ? t("scenario:cityPlaceholder") : value}
      groups={[{ key: "cities", label: t("scenario:cities"), items }]}
      onQuery={setQuery}
      onSelect={(item: ComboboxItem) => onSelect(item.value)}
      emptyText={t("scenario:noMatches")}
      className={className}
    />
  )
}
