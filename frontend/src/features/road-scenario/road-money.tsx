import type { RoadJob } from "@/shared/api/road-graph"
import { useTranslation } from "@/shared/i18n"
import { Stat } from "@/shared/ui"
import styles from "./road-scenario.module.css"

export function RoadMoney({ job }: { readonly job: RoadJob }) {
  const { t } = useTranslation()
  const money = job.result?.money
  if (!money)
    return (
      <p className={styles.note}>
        {t(job.money_assumptions ? "graph:moneyUnavailable" : "graph:moneyPrompt")}
      </p>
    )
  const a = money.assumptions
  return (
    <div className={styles.result}>
      <p className={styles.note}>{t("graph:moneyMethod")}</p>
      <Stat
        label={t("graph:moneyGross")}
        value={t("graph:rubles", { value: money.annual_gross_rub })}
      />
      <Stat
        label={t("graph:moneyNet")}
        value={t("graph:rubles", { value: money.annual_net_rub })}
      />
      <p className={styles.note}>
        {t("graph:moneyFlow", {
          origin: a.origin_point_id,
          target: a.market_city,
          trips: a.trips_per_year,
          rate: a.rub_per_hour,
          hours: money.hours_saved_per_trip,
        })}
      </p>
      <p className={styles.note}>
        {t("graph:moneyCosts", {
          capital: a.capital_cost_rub,
          operating: a.annual_operating_cost_rub,
        })}
      </p>
      {money.simple_payback_years !== null && money.simple_payback_years !== undefined ? (
        <Stat
          label={t("graph:payback")}
          value={t("graph:years", { value: money.simple_payback_years })}
        />
      ) : null}
    </div>
  )
}
