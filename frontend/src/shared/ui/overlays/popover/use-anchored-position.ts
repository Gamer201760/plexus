import { type CSSProperties, type RefObject, useLayoutEffect, useState } from "react"
import { readPixels } from "../../../motion"
import { type PopoverAlign, type PopoverSide, placeFloating } from "./anchored-position"

export interface AnchoredOptions {
  readonly active: boolean
  readonly side: PopoverSide
  readonly align: PopoverAlign
  readonly matchWidth: boolean
}

export interface AnchoredPosition {
  readonly side: PopoverSide
  readonly style: CSSProperties | undefined
}

function measure(
  anchor: HTMLElement,
  floating: HTMLElement,
  options: AnchoredOptions,
): AnchoredPosition {
  const rect = anchor.getBoundingClientRect()
  const placement = placeFloating({
    anchor: { top: rect.top, left: rect.left, width: rect.width, height: rect.height },
    floating: { width: floating.offsetWidth, height: floating.scrollHeight },
    viewport: { width: window.innerWidth, height: window.innerHeight },
    gap: readPixels("--space-4"),
    margin: readPixels("--space-8"),
    side: options.side,
    align: options.align,
    matchWidth: options.matchWidth,
  })
  const style: CSSProperties = {
    top: placement.top,
    left: placement.left,
    maxBlockSize: placement.maxHeight,
    maxInlineSize: placement.maxWidth,
    ...(placement.minWidth === null ? {} : { minInlineSize: placement.minWidth }),
  }
  return { side: placement.side, style }
}

export function useAnchoredPosition(
  anchorRef: RefObject<HTMLElement | null>,
  floatingRef: RefObject<HTMLElement | null>,
  options: AnchoredOptions,
): AnchoredPosition {
  const { active, side, align, matchWidth } = options
  const [position, setPosition] = useState<AnchoredPosition>({ side, style: undefined })

  useLayoutEffect(() => {
    if (!active) return
    let frame = 0
    const update = () => {
      const anchor = anchorRef.current
      const floating = floatingRef.current
      if (anchor === null || floating === null) return
      setPosition(measure(anchor, floating, { active, side, align, matchWidth }))
    }
    const schedule = () => {
      cancelAnimationFrame(frame)
      frame = requestAnimationFrame(update)
    }
    update()
    window.addEventListener("resize", schedule)
    window.addEventListener("scroll", schedule, { capture: true, passive: true })
    const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(schedule)
    if (floatingRef.current !== null) observer?.observe(floatingRef.current)
    return () => {
      cancelAnimationFrame(frame)
      observer?.disconnect()
      window.removeEventListener("resize", schedule)
      window.removeEventListener("scroll", schedule, { capture: true })
    }
  }, [active, side, align, matchWidth, anchorRef, floatingRef])

  return position
}
