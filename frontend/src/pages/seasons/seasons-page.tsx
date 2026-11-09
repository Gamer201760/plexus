import { useState } from "react"
import { useWinterRoads } from "@/entities/reference"
import { useDocumentTitle, useTranslation } from "@/shared/i18n"
import { ErrorState, PageHeader, Select, Skeleton } from "@/shared/ui"
import { RoadList } from "./road-list"
import { groupBySeason } from "./season-time"
import { SeasonTimeline } from "./season-timeline"
import styles from "./seasons-page.module.css"

const ALL = "all-districts"

export function SeasonsPage() {
  const { t } = useTranslation()
  useDocumentTitle(t("seasons:title"))
  const roads = useWinterRoads()
  const [district, setDistrict] = useState(ALL)
  const districts = [
    ...new Set((roads.data ?? []).flatMap((road) => (road.district ? [road.district] : []))),
  ]
  const rows = (roads.data ?? []).filter((road) => district === ALL || road.district === district)
  const groups = groupBySeason(rows)

  const content = roads.data ? (
    <>
      <div className={styles.timelines}>
        {groups.map((group, index) => (
          <SeasonTimeline key={group.year} group={group} motionIndex={index} />
        ))}
      </div>
      <RoadList roads={groups.flatMap((group) => group.roads)} />
    </>
  ) : (
    <div className={styles.timelines} aria-hidden="true">
      <Skeleton lines={9} className={styles.bone} />
      <Skeleton lines={9} className={styles.bone} />
    </div>
  )

  return (
    <div className={styles.page} aria-busy={roads.data === undefined}>
      <PageHeader
        title={t("seasons:title")}
        description={t("seasons:lead")}
        actions={
          <Select
            label={t("seasons:district")}
            hideLabel
            value={district}
            onChange={setDistrict}
            options={[
              { value: ALL, label: t("seasons:allDistricts") },
              ...districts.map((name) => ({ value: name, label: name })),
            ]}
          />
        }
      />
      {roads.isError ? (
        <ErrorState title={t("errors:kind.server")} onRetry={() => void roads.refetch()} />
      ) : (
        content
      )}
    </div>
  )
}
