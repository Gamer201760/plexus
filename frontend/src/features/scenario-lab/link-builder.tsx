import { useState } from "react"
import type { MarketCity, ScenarioMode } from "@/entities/scenario"
import { useTranslation } from "@/shared/i18n"
import { Button, Chip, NumberField, Select } from "@/shared/ui"
import styles from "./link-builder.module.css"
import { PlacePicker } from "./place-picker"
import {
  isScheduled,
  LINK_LIMIT,
  type LinkDraft,
  parseTravel,
  validFrequency,
} from "./use-scenario-lab"

export interface LinkBuilderProps {
  readonly cities: readonly MarketCity[]
  readonly links: readonly LinkDraft[]
  readonly onAdd: (draft: LinkDraft) => void
  readonly onRemove: (index: number) => void
}

const EMPTY: LinkDraft = {
  from: "",
  fromLabel: "",
  to: "",
  toLabel: "",
  mode: "air",
  travel: "",
  frequency: "",
}
const MODES: readonly ScenarioMode[] = ["air", "rail", "road"]

export function LinkBuilder({ cities, links, onAdd, onRemove }: LinkBuilderProps) {
  const { t } = useTranslation()
  const [draft, setDraft] = useState<LinkDraft>(EMPTY)
  const travelInvalid = draft.travel !== "" && parseTravel(draft.travel) === null
  const frequencyInvalid = !validFrequency(draft)
  const complete =
    draft.from !== "" &&
    draft.to !== "" &&
    draft.from !== draft.to &&
    parseTravel(draft.travel) !== null &&
    !frequencyInvalid
  const full = links.length >= LINK_LIMIT
  return (
    <div className={styles.builder}>
      <PlacePicker
        label={t("scenario:from")}
        cities={cities}
        value={draft.from === "" ? null : { id: draft.from, label: draft.fromLabel }}
        exclude={draft.to}
        onSelect={(choice) => setDraft({ ...draft, from: choice.id, fromLabel: choice.label })}
      />
      <PlacePicker
        label={t("scenario:to")}
        cities={cities}
        value={draft.to === "" ? null : { id: draft.to, label: draft.toLabel }}
        exclude={draft.from}
        onSelect={(choice) => setDraft({ ...draft, to: choice.id, toLabel: choice.label })}
      />
      <Select
        label={t("scenario:mode")}
        value={draft.mode}
        onChange={(mode) => setDraft({ ...draft, mode, frequency: "" })}
        options={MODES.map((mode) => ({ value: mode, label: t(`scenario:modes.${mode}`) }))}
      />
      <NumberField
        label={t("scenario:travel")}
        icon="route"
        value={draft.travel}
        onChange={(event) => setDraft({ ...draft, travel: event.currentTarget.value })}
        error={travelInvalid ? t("scenario:travelError") : undefined}
      />
      {isScheduled(draft.mode) && (
        <NumberField
          label={t("scenario:frequency")}
          icon="calendar"
          value={draft.frequency}
          onChange={(event) => setDraft({ ...draft, frequency: event.currentTarget.value })}
          error={frequencyInvalid ? t("scenario:frequencyError") : undefined}
          hint={t("scenario:frequencyHint")}
        />
      )}
      <Button
        icon="plus"
        disabled={!complete || full}
        onClick={() => {
          onAdd(draft)
          setDraft(EMPTY)
        }}
      >
        {t("scenario:add")}
      </Button>
      {full && <p className={styles.note}>{t("scenario:limit")}</p>}
      {links.length > 0 && (
        <ul className={styles.chips} aria-label={t("scenario:links")}>
          {links.map((link, index) => (
            <li key={`${link.from}-${link.to}-${link.mode}`}>
              <Chip pressed onPressedChange={() => onRemove(index)} icon="route">
                {t("scenario:linkRow", { from: link.fromLabel, to: link.toLabel })}
              </Chip>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
