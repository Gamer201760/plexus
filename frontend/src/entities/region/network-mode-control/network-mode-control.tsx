import { useNetworkMode } from "@/shared/hooks/use-network-mode"
import { useTranslation } from "@/shared/i18n"
import { Select } from "@/shared/ui"

export function NetworkModeControl() {
  const { t } = useTranslation()
  const { networkMode, setNetworkMode } = useNetworkMode()
  return (
    <Select
      label={t("data:network.label")}
      value={networkMode}
      onChange={setNetworkMode}
      options={[
        { value: "road", label: t("data:network.road") },
        { value: "multimodal", label: t("data:network.multimodal") },
      ]}
    />
  )
}
