import { type RefObject, useEffect, useRef } from "react"

export interface DismissOptions {
  readonly open: boolean
  readonly onClose: () => void
  readonly anchorRef: RefObject<HTMLElement | null>
  readonly floatingRef: RefObject<HTMLElement | null>
  readonly focusOnOpen: boolean
}

function contains(ref: RefObject<HTMLElement | null>, target: EventTarget | null): boolean {
  return target instanceof Node && ref.current?.contains(target) === true
}

export function useDismiss({ open, onClose, anchorRef, floatingRef, focusOnOpen }: DismissOptions) {
  const closeRef = useRef(onClose)
  closeRef.current = onClose

  useEffect(() => {
    if (!open) return
    const onPointerDown = (event: PointerEvent) => {
      if (contains(anchorRef, event.target) || contains(floatingRef, event.target)) return
      closeRef.current()
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return
      event.stopPropagation()
      closeRef.current()
    }
    document.addEventListener("pointerdown", onPointerDown, true)
    document.addEventListener("keydown", onKeyDown, true)
    return () => {
      document.removeEventListener("pointerdown", onPointerDown, true)
      document.removeEventListener("keydown", onKeyDown, true)
    }
  }, [open, anchorRef, floatingRef])

  useEffect(() => {
    if (!open) return
    if (focusOnOpen) floatingRef.current?.focus()
    return () => {
      const active = document.activeElement
      const lost = active === null || active === document.body
      if (lost || contains(floatingRef, active)) anchorRef.current?.focus()
    }
  }, [open, focusOnOpen, anchorRef, floatingRef])
}
