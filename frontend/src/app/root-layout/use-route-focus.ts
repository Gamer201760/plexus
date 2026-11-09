import { useEffect, useRef } from "react"
import { useLocation } from "react-router"

export function useRouteFocus(): void {
  const { pathname } = useLocation()
  const previous = useRef<string | null>(null)
  useEffect(() => {
    const changed = previous.current !== null && previous.current !== pathname
    previous.current = pathname
    if (!changed) return
    const frame = window.requestAnimationFrame(() => {
      const focused = document.activeElement
      if (focused instanceof HTMLInputElement) return
      const target =
        document.querySelector<HTMLElement>("#main h1") ??
        document.querySelector<HTMLElement>("#main")
      target?.focus({ preventScroll: true })
    })
    return () => window.cancelAnimationFrame(frame)
  }, [pathname])
}
