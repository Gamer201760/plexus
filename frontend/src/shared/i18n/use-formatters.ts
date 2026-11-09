import { useMemo } from "react"
import { createFormatters, type Formatters } from "./formatters"

export function useFormatters(): Formatters {
  return useMemo(() => createFormatters(), [])
}
