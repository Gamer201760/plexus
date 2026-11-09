import type { CSSProperties } from "react"
import { useFormatters, useTranslation } from "@/shared/i18n"
import styles from "./composition-cell.module.css"
import type { TransportGroup } from "./transport-groups"
export interface CompositionCellProps {
  readonly values: readonly { key: TransportGroup; value: number }[]
  readonly max: number
}
export function CompositionCell({ values, max }: CompositionCellProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  return (
    <div className={styles.composition}>
      <span className={styles.stack} aria-hidden="true">
        {values.map((v) => (
          <i
            key={v.key}
            data-mode={v.key}
            style={{ "--bar-width": `${(v.value / Math.max(1, max)) * 100}%` } as CSSProperties}
          />
        ))}
      </span>
      <span>{f.integer(values.reduce((s, v) => s + v.value, 0))}</span>
      <span className="visually-hidden">
        {values
          .map((v) => t("atlas:modeCount", { mode: t(`atlas:groups.${v.key}`), count: v.value }))
          .join(", ")}
      </span>
    </div>
  )
}
