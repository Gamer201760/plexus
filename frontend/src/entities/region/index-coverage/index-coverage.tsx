import { useFormatters, useTranslation } from "@/shared/i18n"
import { NoValue, Tooltip } from "@/shared/ui"

export interface IndexCoverageProps {
  readonly value: number | null | undefined
  readonly compact?: boolean
}

export function IndexCoverage({ value, compact = false }: IndexCoverageProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  if (value === null || value === undefined) return <NoValue />
  return (
    <Tooltip content={t("data:network.coverageHint")}>
      <span>
        {compact ? f.percent(value, 1) : t("data:network.coverage", { value: f.percent(value, 1) })}
      </span>
    </Tooltip>
  )
}
