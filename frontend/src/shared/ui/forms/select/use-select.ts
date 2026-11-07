import { type KeyboardEvent, useState } from "react"
import { isPrintableKey, useTypeahead } from "./use-typeahead"

type Move = (index: number, last: number) => number

const PAGE = 10

const CLOSED_KEYS: Readonly<Record<string, Move>> = {
  ArrowDown: (index) => Math.max(index, 0),
  ArrowUp: (index, last) => (index < 0 ? last : index),
  Enter: (index) => Math.max(index, 0),
  " ": (index) => Math.max(index, 0),
  Home: () => 0,
  End: (_index, last) => last,
}

const OPEN_MOVES: Readonly<Record<string, Move>> = {
  ArrowDown: (index, last) => Math.min(index + 1, last),
  ArrowUp: (index) => Math.max(index - 1, 0),
  Home: () => 0,
  End: (_index, last) => last,
  PageDown: (index, last) => Math.min(index + PAGE, last),
  PageUp: (index) => Math.max(index - PAGE, 0),
}

export interface SelectController {
  readonly open: boolean
  readonly activeIndex: number
  readonly setActiveIndex: (index: number) => void
  readonly toggle: () => void
  readonly close: () => void
  readonly pick: (index: number) => void
  readonly onKeyDown: (event: KeyboardEvent<HTMLElement>) => void
}

function modified(event: KeyboardEvent<HTMLElement>): boolean {
  return event.ctrlKey || event.metaKey || event.altKey
}

export function useSelectController(
  labels: readonly string[],
  selectedIndex: number,
  onPick: (index: number) => void,
): SelectController {
  const [open, setOpen] = useState(false)
  const [activeIndex, setActiveIndex] = useState(-1)
  const typeahead = useTypeahead(labels)
  const last = labels.length - 1

  const openAt = (index: number) => {
    setActiveIndex(index)
    setOpen(true)
  }
  const close = () => setOpen(false)
  const pick = (index: number) => {
    setOpen(false)
    onPick(index)
  }
  const toggle = () => (open ? close() : openAt(Math.max(selectedIndex, 0)))

  const onClosedKey = (event: KeyboardEvent<HTMLElement>) => {
    const move = CLOSED_KEYS[event.key]
    if (move !== undefined) {
      event.preventDefault()
      openAt(move(selectedIndex, last))
      return
    }
    if (!isPrintableKey(event.key, modified(event))) return
    event.preventDefault()
    openAt(typeahead.type(event.key, selectedIndex) ?? Math.max(selectedIndex, 0))
  }

  const onCommandKey = (event: KeyboardEvent<HTMLElement>): boolean => {
    if (event.key === "Escape" || event.key === "Tab") {
      if (event.key === "Escape") event.preventDefault()
      close()
      return true
    }
    if (event.key !== "Enter" && (event.key !== " " || typeahead.busy())) return false
    event.preventDefault()
    if (activeIndex >= 0) pick(activeIndex)
    else close()
    return true
  }

  const onOpenKey = (event: KeyboardEvent<HTMLElement>) => {
    const move = OPEN_MOVES[event.key]
    if (move !== undefined) {
      event.preventDefault()
      setActiveIndex(move(activeIndex, last))
      return
    }
    if (onCommandKey(event)) return
    if (event.key !== " " && !isPrintableKey(event.key, modified(event))) return
    event.preventDefault()
    const match = typeahead.type(event.key, activeIndex)
    if (match !== null) setActiveIndex(match)
  }

  const onKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (labels.length === 0) return
    if (open) onOpenKey(event)
    else onClosedKey(event)
  }

  return { open, activeIndex, setActiveIndex, toggle, close, pick, onKeyDown }
}
