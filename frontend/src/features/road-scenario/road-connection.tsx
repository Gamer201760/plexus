import { useState } from "react"
import type { RoadGraphState } from "@/entities/road-graph"
import type { GraphLocation } from "@/shared/api/road-graph"
import { useTranslation } from "@/shared/i18n"
import { Banner, Button, TextField } from "@/shared/ui"
import { ConnectionPlace } from "./connection-place"

export function RoadConnection({
  roads,
  regionId,
}: {
  readonly roads: RoadGraphState
  readonly regionId: string | null
}) {
  const { t } = useTranslation()
  const [source, setSource] = useState<GraphLocation | null>(null)
  const [target, setTarget] = useState<GraphLocation | null>(null)
  const [minutes, setMinutes] = useState("")
  const duration = Number(minutes.replace(",", "."))
  const valid = /^\d+([.,]\d+)?$/.test(minutes.trim()) && duration > 0 && duration <= 4320
  const busy =
    roads.addConnection.isPending ||
    roads.submit.isPending ||
    ["queued", "running"].includes(roads.job?.status ?? "")
  return (
    <>
      <p>{t("graph:connection.hint")}</p>
      <ConnectionPlace
        label={t("graph:connection.from")}
        value={source}
        exclude={target?.node ?? null}
        onSelect={setSource}
      />
      <ConnectionPlace
        label={t("graph:connection.to")}
        value={target}
        exclude={source?.node ?? null}
        onSelect={setTarget}
      />
      <TextField
        label={t("graph:connection.minutes")}
        value={minutes}
        inputMode="decimal"
        onChange={(e) => setMinutes(e.target.value)}
        error={minutes && !valid ? t("graph:connection.invalidTime") : undefined}
      />
      {!regionId ? <p>{t("graph:pickRegion")}</p> : null}
      <Button
        icon="route"
        disabled={
          !regionId ||
          source?.node == null ||
          target?.node == null ||
          source.node === target.node ||
          !valid ||
          busy
        }
        onClick={() => {
          if (
            regionId &&
            source?.node != null &&
            target?.node != null &&
            source.node !== target.node &&
            valid
          )
            roads.addConnection.mutate({
              region_id: regionId,
              source_node: source.node,
              target_node: target.node,
              travel_hours: duration / 60,
            })
        }}
      >
        {t("graph:connection.calculate")}
      </Button>
      {roads.addConnection.isError ? (
        <Banner tone="danger" title={t("graph:requestError")} />
      ) : null}
    </>
  )
}
