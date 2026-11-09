import { useSeason } from "@/shared/hooks/use-season"
import { useTranslation } from "@/shared/i18n"
import { Segmented } from "@/shared/ui"
export function SeasonControl() {
  const { t } = useTranslation()
  const { season, setSeason } = useSeason()
  return (
    <Segmented
      label={t("data:season.legend")}
      value={season}
      onChange={setSeason}
      options={[
        { value: "summer", label: t("data:season.summer"), icon: "sun" },
        { value: "winter", label: t("data:season.winter"), icon: "snowflake" },
      ]}
    />
  )
}
