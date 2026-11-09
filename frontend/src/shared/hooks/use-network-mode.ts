import { useSearchParams } from "react-router"
import type { components } from "@/shared/api"

export type NetworkMode = components["schemas"]["NetworkMode"]

export function useNetworkMode() {
  const [params, setParams] = useSearchParams()
  const networkMode: NetworkMode =
    params.get("network_mode") === "multimodal" ? "multimodal" : "road"
  const setNetworkMode = (value: NetworkMode) =>
    setParams(
      (current) => {
        const next = new URLSearchParams(current)
        next.set("network_mode", value)
        return next
      },
      { replace: true },
    )
  return { networkMode, setNetworkMode }
}
