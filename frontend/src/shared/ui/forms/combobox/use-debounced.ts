import { useCallback, useEffect, useRef } from "react"
import { motionMs } from "../../../motion"

export function useDebounced<T>(callback: (value: T) => void): (value: T) => void {
  const latest = useRef(callback)
  const timer = useRef<number | undefined>(undefined)
  latest.current = callback

  useEffect(() => () => window.clearTimeout(timer.current), [])

  return useCallback((value: T) => {
    window.clearTimeout(timer.current)
    timer.current = window.setTimeout(() => latest.current(value), motionMs("--delay-debounce"))
  }, [])
}
