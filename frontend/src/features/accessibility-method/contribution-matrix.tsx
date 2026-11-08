import { type CSSProperties, useState } from "react"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Button } from "@/shared/ui"
import styles from "./contribution-matrix.module.css"

const MARKETS = [13000, 50000, 100000, 250000, 500000, 1000000, 5000000]
const HOURS = [0, 1, 2, 3, 4, 6, 8]
export interface ContributionMatrixProps {
  readonly halfLife: number
}
export function ContributionMatrix({ halfLife }: ContributionMatrixProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const [selected, setSelected] = useState({ market: 1000000, hours: 6 })
  const valueAt = (market: number, hours: number) => market * 2 ** (-hours / halfLife)
  const min = Math.log10(valueAt(MARKETS[0] ?? 13000, 8))
  const max = Math.log10(5000000)
  const bin = (value: number) =>
    Math.min(7, 1 + Math.floor(((Math.log10(value) - min) / (max - min)) * 7))
  return (
    <div className={styles.matrix}>
      <table>
        <caption className="visually-hidden">{t("method:matrixTitle")}</caption>
        <thead>
          <tr>
            <th>{t("method:marketSize")}</th>
            {HOURS.map((h) => (
              <th key={h}>{t("method:hours", { value: h })}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {MARKETS.map((m) => (
            <tr key={m}>
              <th scope="row">{f.compact(m)}</th>
              {HOURS.map((h) => {
                const value = valueAt(m, h)
                return (
                  <td key={h}>
                    <Button
                      variant="ghost"
                      className={styles.cell}
                      style={
                        {
                          "--cell-background": `var(--data-seq-${bin(value)})`,
                          "--cell-color":
                            bin(value) >= 6 ? "var(--text-on-inverse)" : "var(--text-primary)",
                        } as CSSProperties
                      }
                      aria-label={t("method:example", {
                        market: f.compact(m),
                        hours: h,
                        value: f.compact(Math.round(value)),
                      })}
                      aria-pressed={selected.market === m && selected.hours === h}
                      onClick={() => setSelected({ market: m, hours: h })}
                    >
                      {f.compact(Math.round(value))}
                    </Button>
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <p className={styles.readout} aria-live="polite">
        {t("method:example", {
          market: f.compact(selected.market),
          hours: selected.hours,
          value: f.compact(Math.round(valueAt(selected.market, selected.hours))),
        })}
      </p>
      <p className={styles.note}>{t("method:illustration")}</p>
    </div>
  )
}
