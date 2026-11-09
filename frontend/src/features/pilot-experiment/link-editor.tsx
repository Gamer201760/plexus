import type { Pilot, PilotEdge } from "@/entities/pilot"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Icon, NumberField, Switch } from "@/shared/ui"
import styles from "./link-editor.module.css"
import type { LinkDraft } from "./use-experiment"

export interface LinkEditorProps {
  readonly pilot: Pilot
  readonly edge: PilotEdge
  readonly season: string
  readonly draft: LinkDraft
  readonly onChange: (draft: LinkDraft) => void
}

export function LinkEditor({ pilot, edge, season, draft, onChange }: LinkEditorProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const name = (id: string) => pilot.points.find((point) => point.id === id)?.name ?? id
  const invalid =
    draft.frequency !== "" &&
    (!/^\d+$/.test(draft.frequency) || Number(draft.frequency) < 1 || Number(draft.frequency) > 28)
  const active = edge.seasons.includes(season)
  const frequency = edge.frequency_per_week
  const assumed = edge.assumed_frequency_per_week
  return (
    <li className={styles.row} data-inactive={!active}>
      <p className={styles.title}>
        {t("pilot:routeTitle", { from: name(edge.from_id), to: name(edge.to_id) })}
      </p>
      <p className={styles.meta}>
        {t(`pilot:modes.${edge.mode as "air" | "river" | "winter_road" | "road"}`)}
      </p>
      <Switch
        label={t("pilot:enabled")}
        checked={draft.enabled}
        disabled={!edge.editable}
        onChange={(enabled) => onChange({ ...draft, enabled })}
      />
      {!active && <p className={styles.note}>{t("pilot:inactive")}</p>}
      {edge.frequency_editable && (
        <NumberField
          label={t("pilot:frequency")}
          icon="calendar"
          value={draft.frequency}
          onChange={(event) => onChange({ ...draft, frequency: event.currentTarget.value })}
          disabled={!draft.enabled}
          error={invalid ? t("pilot:frequencyError") : undefined}
          hint={
            frequency !== null
              ? t("pilot:sourceFrequency", { count: frequency })
              : assumed !== null
                ? t("pilot:unknownFrequency", { count: assumed })
                : t("pilot:unknown")
          }
        />
      )}
      {!edge.frequency_editable && frequency !== null && (
        <p className={styles.note}>{t("pilot:sourceFrequency", { count: frequency })}</p>
      )}
      {edge.edit_disabled_reason === "source_frequency_out_of_range" && (
        <p className={styles.note}>{t("pilot:notEditableFrequency")}</p>
      )}
      <p className={styles.note}>
        {t("pilot:movement")}: {f.number(edge.travel_h, 2)}
      </p>
      <div className={styles.source}>
        <a href={edge.source_url} target="_blank" rel="noreferrer">
          <Icon name="external" size="sm" />
          {t("pilot:source")}
        </a>
        <span>
          {edge.source_period
            ? t("pilot:period", { period: edge.source_period })
            : t("pilot:noPeriod")}
        </span>
      </div>
    </li>
  )
}
