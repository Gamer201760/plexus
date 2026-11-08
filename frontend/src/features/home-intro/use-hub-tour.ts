import { useEffect, useState } from "react"
import { motionMs, useReducedMotion } from "@/shared/motion"

export function useHubTour(size: number, paused: boolean): number | null {
  const reduced = useReducedMotion()
  const [active, setActive] = useState<number | null>(null)

  useEffect(() => {
    if (size === 0) return
    if (reduced) {
      setActive((current) => current ?? 0)
      return
    }
    if (paused) return
    const start = window.setTimeout(
      () => setActive((current) => current ?? 0),
      motionMs("--dur-draw") * 2,
    )
    const step = window.setInterval(
      () => setActive((current) => ((current ?? -1) + 1) % size),
      motionMs("--dur-tour"),
    )
    return () => {
      window.clearTimeout(start)
      window.clearInterval(step)
    }
  }, [size, paused, reduced])

  return active
}
