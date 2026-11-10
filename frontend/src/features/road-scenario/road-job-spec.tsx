import type { RoadJob } from "@/shared/api/road-graph"
import { useTranslation } from "@/shared/i18n"
import { Disclosure } from "@/shared/ui"
import styles from "./road-scenario.module.css"

export function RoadJobSpec({ job }: { readonly job: RoadJob }) {
  const { t } = useTranslation()
  if (job.addition)
    return (
      <p className={styles.note}>
        {t("graph:addition", {
          source: job.addition.source_node,
          target: job.addition.target_node,
          minutes: job.addition.travel_hours * 60,
        })}
      </p>
    )
  return (
    <>
      <p className={styles.note}>
        {t("graph:jobSpec", {
          scenario: t(scenarioLabel(job.scenario)),
          count: job.changes.length,
        })}
      </p>
      <Disclosure title={t("graph:changedRoads")} defaultOpen={job.changes.length <= 5}>
        <ul className={styles.changes}>
          {job.changes.map((change) => (
            <li key={change.way_id}>
              {t("graph:change", { id: change.way_id, factor: change.speed_factor })}
            </li>
          ))}
        </ul>
      </Disclosure>
    </>
  )
}

function scenarioLabel(value: string) {
  if (value === "road") return "graph:base"
  return value === "summer" ? "graph:summer" : "graph:winter"
}
