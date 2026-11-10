import type { RoadJob } from "@/shared/api/road-graph"
import { useTranslation } from "@/shared/i18n"
import { DataTable } from "@/shared/ui"

export function SettlementEffects({ result }: { readonly result: NonNullable<RoadJob["result"]> }) {
  const { t } = useTranslation()
  if (!result.settlement_effects?.length) return null
  return (
    <>
      <p>{t("graph:connection.effectHint", { count: result.affected_settlements ?? 0 })}</p>
      <DataTable
        caption={t("graph:connection.effects")}
        rows={result.settlement_effects}
        rowKey={(r) => r.point_id}
        columns={[
          { key: "point_id", header: t("graph:connection.point"), cell: (r) => r.point_id },
          {
            key: "before",
            header: t("graph:before"),
            cell: (r) => t("graph:number", { value: r.before }),
          },
          {
            key: "after",
            header: t("graph:after"),
            cell: (r) => t("graph:number", { value: r.after }),
          },
          {
            key: "delta",
            header: t("graph:delta"),
            cell: (r) => t("graph:number", { value: r.delta }),
          },
        ]}
      />
    </>
  )
}
