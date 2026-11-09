import { useCallback, useMemo } from "react"
import { useSearchParams } from "react-router"

export const COMPARE_LIMIT = 4

function parseIds(raw: string | null): readonly string[] {
  if (raw === null || raw === "") return []
  return [...new Set(raw.split(",").filter((id) => id !== ""))].slice(0, COMPARE_LIMIT)
}

export function useCompareParams() {
  const [params, setParams] = useSearchParams()
  const ids = useMemo(() => parseIds(params.get("ids")), [params])

  const write = useCallback(
    (next: readonly string[]) =>
      setParams(
        (current) => {
          const updated = new URLSearchParams(current)
          if (next.length === 0) updated.delete("ids")
          else updated.set("ids", next.join(","))
          return updated
        },
        { replace: true, preventScrollReset: true },
      ),
    [setParams],
  )

  const add = useCallback(
    (id: string) => {
      if (ids.includes(id) || ids.length >= COMPARE_LIMIT) return
      write([...ids, id])
    },
    [ids, write],
  )

  const remove = useCallback((id: string) => write(ids.filter((item) => item !== id)), [ids, write])

  return { ids, add, remove }
}
