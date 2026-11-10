import { useState } from "react"
import type { Pilot } from "@/entities/pilot"
import { useTranslation } from "@/shared/i18n"
import { Button, Chip, NumberField, Select } from "@/shared/ui"
import styles from "./route-adder.module.css"
import {
  ADDITION_LIMIT,
  type AdditionDraft,
  type AdditionMode,
  additionRequest,
  additionScheduled,
  parseTravel,
} from "./use-experiment"

export interface RouteAdderProps {
  readonly pilot: Pilot
  readonly additions: readonly AdditionDraft[]
  readonly onAdd: (draft: AdditionDraft) => void
  readonly onRemove: (index: number) => void
}

const EMPTY: AdditionDraft = { from: "", to: "", mode: "air", travel: "", frequency: "" }
const MODES: readonly AdditionMode[] = ["air", "road", "river", "winter_road"]

export function RouteAdder({ pilot, additions, onAdd, onRemove }: RouteAdderProps) {
  const { t } = useTranslation()
  const [draft, setDraft] = useState<AdditionDraft>(EMPTY)
  const name = (id: string) => pilot.points.find((point) => point.id === id)?.name ?? id
  const points = (exclude: string) =>
    pilot.points
      .filter((point) => point.id !== exclude)
      .map((point) => ({ value: point.id, label: point.name }))
  const travelInvalid = draft.travel !== "" && parseTravel(draft.travel) === null
  const frequencyInvalid =
    additionScheduled(draft.mode) &&
    draft.frequency !== "" &&
    (!/^\d+$/.test(draft.frequency) || Number(draft.frequency) < 1 || Number(draft.frequency) > 28)
  const full = additions.length >= ADDITION_LIMIT
  return (
    <div className={styles.adder}>
      <p className={styles.title}>{t("pilot:newLink")}</p>
      <p className={styles.hint}>{t("pilot:newLinkHint")}</p>
      <Select
        label={t("pilot:from")}
        value={draft.from === "" ? null : draft.from}
        placeholder={t("pilot:pointPlaceholder")}
        options={points(draft.to)}
        onChange={(from) => setDraft({ ...draft, from })}
      />
      <Select
        label={t("pilot:to")}
        value={draft.to === "" ? null : draft.to}
        placeholder={t("pilot:pointPlaceholder")}
        options={points(draft.from)}
        onChange={(to) => setDraft({ ...draft, to })}
      />
      <Select
        label={t("pilot:addMode")}
        value={draft.mode}
        options={MODES.map((mode) => ({ value: mode, label: t(`pilot:modes.${mode}`) }))}
        onChange={(mode) => setDraft({ ...draft, mode, frequency: "" })}
      />
      <NumberField
        label={t("pilot:addTravel")}
        icon="route"
        value={draft.travel}
        onChange={(event) => setDraft({ ...draft, travel: event.currentTarget.value })}
        error={travelInvalid ? t("pilot:addTravelError") : undefined}
      />
      {additionScheduled(draft.mode) && (
        <NumberField
          label={t("pilot:frequency")}
          icon="calendar"
          value={draft.frequency}
          onChange={(event) => setDraft({ ...draft, frequency: event.currentTarget.value })}
          error={frequencyInvalid ? t("pilot:frequencyError") : undefined}
        />
      )}
      <Button
        icon="plus"
        variant="secondary"
        disabled={additionRequest(draft) === null || full}
        onClick={() => {
          onAdd(draft)
          setDraft(EMPTY)
        }}
      >
        {t("pilot:add")}
      </Button>
      {additions.length > 0 && (
        <ul className={styles.chips} aria-label={t("pilot:added")}>
          {additions.map((addition, index) => (
            <li key={`${addition.from}-${addition.to}-${addition.mode}`}>
              <Chip pressed onPressedChange={() => onRemove(index)} icon="route">
                {t("pilot:routeTitle", { from: name(addition.from), to: name(addition.to) })}
              </Chip>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
