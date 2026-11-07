import { type KeyboardEvent, type RefObject, useEffect } from "react"

const TABBABLE = [
  "a[href]",
  "button:not(:disabled)",
  "input:not(:disabled)",
  "textarea:not(:disabled)",
  '[tabindex]:not([tabindex="-1"])',
].join(",")

export function tabbables(root: HTMLElement): HTMLElement[] {
  return [...root.querySelectorAll<HTMLElement>(TABBABLE)]
    .filter((element) => !element.hasAttribute("hidden") && element.closest("[inert]") === null)
    .sort((first, second) =>
      first.compareDocumentPosition(second) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1,
    )
}

export function trapTab(event: KeyboardEvent<HTMLElement>, root: HTMLElement): void {
  if (event.key !== "Tab") return
  const items = tabbables(root)
  const first = items[0]
  const last = items.at(-1)
  if (first === undefined || last === undefined) {
    event.preventDefault()
    return
  }
  const active = document.activeElement
  const outside = active === null || !items.includes(active as HTMLElement)
  if (event.shiftKey && (active === first || outside)) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && active === last) {
    event.preventDefault()
    first.focus()
  }
}

export function useModalFocus(open: boolean, titleRef: RefObject<HTMLElement | null>): void {
  useEffect(() => {
    if (!open) return
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null
    titleRef.current?.focus()
    return () => {
      if (previous?.isConnected) previous.focus()
    }
  }, [open, titleRef])

  useEffect(() => {
    if (!open) return
    const root = document.documentElement
    const previous = root.style.overflow
    root.style.overflow = "hidden"
    return () => {
      root.style.overflow = previous
    }
  }, [open])
}
