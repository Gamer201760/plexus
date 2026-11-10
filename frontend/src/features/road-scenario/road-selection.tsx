import type { RoadGraphState } from "@/entities/road-graph"
import { useTranslation } from "@/shared/i18n"
import { Banner, Button, Card, Skeleton, Switch } from "@/shared/ui"
import styles from "./road-scenario.module.css"

export function RoadSelection({ roads }: { readonly roads: RoadGraphState }) {
  const { t } = useTranslation()
  const available = roads.view.data?.segments ?? []
  return (
    <>
      <Switch label={t("graph:layer")} checked={roads.enabled} onChange={roads.setEnabled} />
      <p className={styles.note}>{t("graph:method")}</p>
      <p className={styles.note}>{t("graph:mapKey")}</p>
      <p className={styles.note}>{t("graph:addHint")}</p>
      {roads.view.isFetching || roads.rendering ? (
        <p role="status" className={styles.note}>
          {t("graph:updating")}
        </p>
      ) : null}
      {roads.view.isLoading ? <Skeleton lines={2} /> : null}
      {roads.view.isError ? (
        <Banner
          tone="danger"
          title={t("graph:loadError")}
          action={<Button onClick={() => roads.view.refetch()}>{t("common:action.retry")}</Button>}
        />
      ) : null}
      {roads.enabled && roads.view.data ? (
        <p className={styles.note}>
          {t("graph:coverage", {
            count: roads.view.data.segmentCount,
            total: roads.view.data.matched,
            detail: t(detailKey(roads.view.data.detail ?? "all")),
          })}
        </p>
      ) : null}
      <Card as="div" title={t("graph:selection", { count: roads.selected.length })}>
        <p className={styles.note}>{t("graph:selectHint")}</p>
        <div className={styles.roads}>
          {roads.selected.map((road) => (
            <Button wrap key={road.way_id} variant="secondary" onClick={() => roads.onRoad(road)}>
              {t("graph:removeRoad", { name: road.name, id: road.way_id })}
            </Button>
          ))}
          {roads.selected.length === 0
            ? available.map((road) => (
                <Button wrap key={road.way_id} variant="ghost" onClick={() => roads.onRoad(road)}>
                  {t("graph:addRoad", { name: road.name, id: road.way_id })}
                </Button>
              ))
            : null}
        </div>
      </Card>
    </>
  )
}

function detailKey(value: string) {
  const keys = {
    motorway: "graph:detailMotorway",
    trunk: "graph:detailTrunk",
    primary: "graph:detailPrimary",
    secondary: "graph:detailSecondary",
    tertiary: "graph:detailTertiary",
    all: "graph:detailAll",
  } as const
  return value in keys ? keys[value as keyof typeof keys] : "graph:detailAll"
}
