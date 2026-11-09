import { useMemo, useState } from "react"
import type { RegionSummary } from "@/entities/region"
import { useTranslation } from "@/shared/i18n"
import { Chip, Combobox, type ComboboxItem } from "@/shared/ui"
import styles from "./region-picker.module.css"
import { COMPARE_LIMIT } from "./use-compare-params"

export interface RegionPickerProps {
  readonly regions: readonly RegionSummary[]
  readonly ids: readonly string[]
  readonly onAdd: (id: string) => void
  readonly onRemove: (id: string) => void
}

const SUGGESTIONS = 8

export function RegionPicker({ regions, ids, onAdd, onRemove }: RegionPickerProps) {
  const { t } = useTranslation()
  const [query, setQuery] = useState("")
  const full = ids.length >= COMPARE_LIMIT
  const items = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase("ru-RU")
    if (needle === "") return []
    return regions
      .filter((region) => !ids.includes(region.id))
      .filter((region) => region.name.toLocaleLowerCase("ru-RU").includes(needle))
      .slice(0, SUGGESTIONS)
      .map((region) => ({ value: region.id, label: region.name }))
  }, [regions, ids, query])
  const selected = ids
    .map((id) => regions.find((region) => region.id === id))
    .filter((region): region is RegionSummary => region !== undefined)
  return (
    <div className={styles.picker}>
      <Combobox
        label={t("compare:picker")}
        hideLabel
        placeholder={full ? t("compare:limit") : t("compare:placeholder")}
        groups={[{ key: "regions", label: t("nav:search.regions"), items }]}
        onQuery={setQuery}
        onSelect={(item: ComboboxItem) => onAdd(item.value)}
        emptyText={t("compare:noMatches")}
        className={styles.field}
      />
      {selected.length > 0 ? (
        <ul className={styles.chips} aria-label={t("compare:selected")}>
          {selected.map((region, index) => (
            <li key={region.id} className={styles.chipSlot} data-series={index + 1}>
              <Chip pressed onPressedChange={() => onRemove(region.id)}>
                {region.name}
              </Chip>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  )
}
