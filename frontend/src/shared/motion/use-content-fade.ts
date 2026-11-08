import { type RefObject, useEffect, useLayoutEffect, useRef } from "react"
import { motionMs, readEasing } from "./css-tokens"
import { useReducedMotion } from "./use-reduced-motion"
export function useContentFade(ref: RefObject<HTMLElement | null>, key: string, instant: boolean) {
  const reduced = useReducedMotion()
  const animation = useRef<Animation | null>(null)
  const previous = useRef(key)
  useLayoutEffect(() => {
    const node = ref.current
    if (!node) return
    const changed = previous.current !== key
    previous.current = key
    const opacity =
      animation.current?.playState === "running" ? getComputedStyle(node).opacity : 0.65
    animation.current?.cancel()
    animation.current = null
    if (!changed || instant || reduced || typeof node.animate !== "function") return
    animation.current = node.animate([{ opacity }, { opacity: 1 }], {
      duration: motionMs("--dur-fast"),
      easing: readEasing("--ease-out"),
    })
  }, [ref, key, instant, reduced])
  useEffect(() => () => animation.current?.cancel(), [])
}
