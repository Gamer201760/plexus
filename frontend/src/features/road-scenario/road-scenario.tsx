import { useState } from "react"
import type { RoadGraphState } from "@/entities/road-graph"
import type { ChatContext } from "@/shared/api/chat-stream"
import { useTranslation } from "@/shared/i18n"
import { Banner, Button, ScrollArea, Segmented, Select, TextField } from "@/shared/ui"
import { RoadConnection } from "./road-connection"
import { RoadResult } from "./road-result"
import styles from "./road-scenario.module.css"
import { RoadSelection } from "./road-selection"

export interface RoadScenarioProps {
  readonly roads: RoadGraphState
  readonly context: ChatContext
}

export function RoadScenario({ roads, context }: RoadScenarioProps) {
  const { t } = useTranslation()
  const [mode, setMode] = useState<"road" | "connection">("road")
  const [factor, setFactor] = useState("1.2")
  const [scenario, setScenario] = useState<"road" | "summer" | "winter">("road")
  const speed = Number(factor.replace(",", "."))
  const valid = factor.trim() !== "" && Number.isFinite(speed) && speed >= 0 && speed <= 3
  const job = roads.job
  const busy =
    roads.addConnection.isPending ||
    roads.submit.isPending ||
    job?.status === "running" ||
    job?.status === "queued"
  return (
    <ScrollArea className={styles.panel} label={t("graph:title")}>
      <Segmented
        label={t("graph:connection.mode")}
        value={mode}
        onChange={setMode}
        options={[
          { value: "road", label: t("graph:connection.editRoad") },
          { value: "connection", label: t("graph:connection.newLink") },
        ]}
      />
      {mode === "connection" ? (
        <RoadConnection roads={roads} regionId={context.region_id ?? null} />
      ) : (
        <>
          <RoadSelection roads={roads} />
          <Select
            label={t("graph:scenario")}
            value={scenario}
            onChange={setScenario}
            options={[
              { value: "road", label: t("graph:base") },
              { value: "summer", label: t("graph:summer") },
              { value: "winter", label: t("graph:winter") },
            ]}
          />
          <TextField
            label={t("graph:factor")}
            value={factor}
            onChange={(event) => setFactor(event.target.value)}
            inputMode="decimal"
            hint={t("graph:factorHint")}
            error={valid ? undefined : t("graph:factorError")}
          />
          {!context.region_id ? <p>{t("graph:pickRegion")}</p> : null}
          <Button
            disabled={!context.region_id || !roads.selected.length || !valid || busy}
            onClick={() => {
              if (context.region_id)
                roads.submit.mutate({
                  region_id: context.region_id,
                  scenario,
                  changes: roads.selected.map((r) => ({ way_id: r.way_id, speed_factor: speed })),
                })
            }}
          >
            {t("graph:calculate")}
          </Button>
        </>
      )}
      {roads.submit.isError || roads.statusError || roads.cancel.isError ? (
        <Banner tone="danger" title={t("graph:requestError")} />
      ) : null}
      {roads.jobs.length > 1 ? (
        <Select
          label={t("graph:history")}
          value={job?.id ?? ""}
          onChange={roads.selectJob}
          options={roads.jobs.map((saved) => ({ value: saved.id, label: saved.region }))}
        />
      ) : null}
      <RoadResult roads={roads} />
    </ScrollArea>
  )
}
