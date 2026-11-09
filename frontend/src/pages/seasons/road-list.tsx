import type { WinterRoad } from "@/entities/reference"
import { useMediaQuery } from "@/shared/hooks"
import { useTranslation } from "@/shared/i18n"
import { Card, DataTable, type DataTableColumn } from "@/shared/ui"
import { useRoadFacts } from "./road-facts"
import styles from "./road-list.module.css"
import { RouteName } from "./route-name"
import { roadKey } from "./season-time"

export interface RoadListProps {
  readonly roads: readonly WinterRoad[]
}

export function RoadList({ roads }: RoadListProps) {
  const { t } = useTranslation()
  const facts = useRoadFacts()
  const narrow = useMediaQuery("(max-width: 48rem)")
  if (narrow)
    return (
      <ul className={styles.cards} aria-label={t("seasons:title")}>
        {roads.map((road) => (
          <li key={roadKey(road)}>
            <Card as="article" title={<RouteName route={road.route} />}>
              <dl className={styles.facts}>
                {facts.map((fact) => (
                  <div key={fact.key} className={styles.fact}>
                    <dt>{fact.label}</dt>
                    <dd>{fact.value(road)}</dd>
                  </div>
                ))}
              </dl>
            </Card>
          </li>
        ))}
      </ul>
    )
  const columns: DataTableColumn<WinterRoad>[] = [
    {
      key: "route",
      header: t("seasons:route"),
      cell: (road) => <RouteName route={road.route} />,
      sortable: true,
      sortValue: (road) => road.route,
    },
    ...facts.map(
      (fact): DataTableColumn<WinterRoad> => ({
        key: fact.key,
        header: fact.label,
        cell: fact.value,
        numeric: fact.numeric,
        sortable: fact.sortValue !== undefined,
        sortValue: fact.sortValue,
      }),
    ),
  ]
  return <DataTable caption={t("seasons:title")} columns={columns} rows={roads} rowKey={roadKey} />
}
