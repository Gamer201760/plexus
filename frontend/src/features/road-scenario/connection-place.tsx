import { useState } from "react"
import { useGraphLocations } from "@/entities/road-graph"
import type { GraphLocation } from "@/shared/api/road-graph"
import { useTranslation } from "@/shared/i18n"
import { Banner, Combobox } from "@/shared/ui"

export function ConnectionPlace({
  label,
  value,
  exclude,
  onSelect,
}: {
  readonly label: string
  readonly value: GraphLocation | null
  readonly exclude: number | null
  readonly onSelect: (value: GraphLocation | null) => void
}) {
  const { t } = useTranslation()
  const [query, setQuery] = useState("")
  const search = useGraphLocations(query)
  const places = (search.data ?? []).filter(
    (place) => place.node !== null && place.node !== exclude,
  )
  return (
    <>
      <Combobox
        label={label}
        minLength={2}
        placeholder={value ? `${value.name}, ${value.region}` : t("graph:connection.search")}
        groups={[
          {
            key: "places",
            label: t("graph:connection.places"),
            items: places.map((place) => ({
              value: place.point_id,
              label: place.name,
              meta: place.region,
            })),
          },
        ]}
        onQuery={(next) => {
          setQuery(next)
          if (next.trim()) onSelect(null)
        }}
        onSelect={(item) => {
          const place = places.find((p) => p.point_id === item.value)
          if (place) onSelect(place)
        }}
        loading={search.isFetching}
        emptyText={t("graph:connection.noMatches")}
      />
      {search.isError ? <Banner tone="danger" title={t("graph:connection.searchError")} /> : null}
    </>
  )
}
