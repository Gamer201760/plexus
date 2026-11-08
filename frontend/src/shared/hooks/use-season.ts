import { useEffect } from "react"
import { useSearchParams } from "react-router"

export type ActiveSeason = "summer" | "winter"
export function useSeason() {
  const [params, setParams] = useSearchParams()
  const raw = params.get("season")
  useEffect(() => {
    if (raw !== null && raw !== "summer" && raw !== "winter")
      setParams(
        (current) => {
          const p = new URLSearchParams(current)
          p.set("season", "winter")
          return p
        },
        { replace: true, preventScrollReset: true, flushSync: true },
      )
  }, [raw, setParams])
  const season: ActiveSeason = params.get("season") === "summer" ? "summer" : "winter"
  const setSeason = (next: ActiveSeason) =>
    setParams(
      (current) => {
        const updated = new URLSearchParams(current)
        updated.set("season", next)
        return updated
      },
      { replace: true, preventScrollReset: true, flushSync: true },
    )
  const seasonHref = (path: string) => `${path}${path.includes("?") ? "&" : "?"}season=${season}`
  return { season, setSeason, seasonHref }
}
