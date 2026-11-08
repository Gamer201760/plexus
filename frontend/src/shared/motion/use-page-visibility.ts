import { useEffect, useState } from "react"

export function usePageVisibility() {
  const [hidden, setHidden] = useState(document.hidden)
  useEffect(() => {
    const sync = () => setHidden(document.hidden)
    document.addEventListener("visibilitychange", sync)
    return () => document.removeEventListener("visibilitychange", sync)
  }, [])
  return hidden
}
