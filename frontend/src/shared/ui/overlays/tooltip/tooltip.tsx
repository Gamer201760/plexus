import {
  cloneElement,
  type FocusEvent,
  type PointerEvent,
  type ReactElement,
  type Ref,
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
} from "react"
import { motionMs, usePresence } from "../../../motion"
import { Layer } from "../layer-host/layer-host"
import type { PopoverSide } from "../popover/anchored-position"
import { useAnchoredPosition } from "../popover/use-anchored-position"
import styles from "./tooltip.module.css"

export interface TooltipTriggerProps {
  readonly ref?: Ref<HTMLElement> | undefined
  readonly "aria-describedby"?: string | undefined
  readonly onPointerEnter?: ((event: PointerEvent<HTMLElement>) => void) | undefined
  readonly onPointerLeave?: ((event: PointerEvent<HTMLElement>) => void) | undefined
  readonly onPointerDown?: ((event: PointerEvent<HTMLElement>) => void) | undefined
  readonly onFocus?: ((event: FocusEvent<HTMLElement>) => void) | undefined
  readonly onBlur?: ((event: FocusEvent<HTMLElement>) => void) | undefined
}

export interface TooltipProps {
  readonly content: string
  readonly side?: PopoverSide
  readonly describe?: boolean
  readonly children: ReactElement<TooltipTriggerProps>
}

const warmth = { hiddenAt: Number.NEGATIVE_INFINITY, visible: 0 }

function isWarm(): boolean {
  return (
    warmth.visible > 0 || performance.now() - warmth.hiddenAt < motionMs("--delay-tooltip-skip")
  )
}

function assignRef<T>(ref: Ref<T> | undefined, value: T | null): void {
  if (typeof ref === "function") ref(value)
  else if (ref !== null && ref !== undefined) ref.current = value
}

function useTooltipState() {
  const [open, setOpen] = useState(false)
  const [instant, setInstant] = useState(false)
  const timer = useRef<number | undefined>(undefined)
  const openRef = useRef(false)

  const reveal = useCallback((warm: boolean) => {
    if (openRef.current) return
    openRef.current = true
    warmth.visible += 1
    setInstant(warm)
    setOpen(true)
  }, [])

  const show = useCallback(() => {
    window.clearTimeout(timer.current)
    if (isWarm()) {
      reveal(true)
      return
    }
    timer.current = window.setTimeout(() => reveal(false), motionMs("--delay-tooltip"))
  }, [reveal])

  const hide = useCallback(() => {
    window.clearTimeout(timer.current)
    if (!openRef.current) return
    openRef.current = false
    warmth.visible -= 1
    warmth.hiddenAt = performance.now()
    setOpen(false)
  }, [])

  useEffect(() => hide, [hide])

  useEffect(() => {
    if (!open) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") hide()
    }
    document.addEventListener("keydown", onKeyDown)
    return () => document.removeEventListener("keydown", onKeyDown)
  }, [open, hide])

  return { open, instant, show, hide }
}

export function Tooltip({ content, side = "top", describe = true, children }: TooltipProps) {
  const id = useId()
  const anchorRef = useRef<HTMLElement | null>(null)
  const bubbleRef = useRef<HTMLSpanElement | null>(null)
  const { open, instant, show, hide } = useTooltipState()
  const presence = usePresence(open)
  const position = useAnchoredPosition(anchorRef, bubbleRef, {
    active: presence.mounted,
    side,
    align: "center",
    matchWidth: false,
  })
  const own = children.props
  const trigger = cloneElement(children, {
    ref: (node: HTMLElement | null) => {
      anchorRef.current = node
      assignRef(own.ref, node)
    },
    "aria-describedby": describe ? id : own["aria-describedby"],
    onPointerEnter: (event: PointerEvent<HTMLElement>) => {
      own.onPointerEnter?.(event)
      if (event.pointerType === "mouse") show()
    },
    onPointerLeave: (event: PointerEvent<HTMLElement>) => {
      own.onPointerLeave?.(event)
      hide()
    },
    onPointerDown: (event: PointerEvent<HTMLElement>) => {
      own.onPointerDown?.(event)
      hide()
    },
    onFocus: (event: FocusEvent<HTMLElement>) => {
      own.onFocus?.(event)
      show()
    },
    onBlur: (event: FocusEvent<HTMLElement>) => {
      own.onBlur?.(event)
      hide()
    },
  })

  return (
    <>
      {trigger}
      {describe ? (
        <span id={id} hidden>
          {content}
        </span>
      ) : null}
      {presence.mounted ? (
        <Layer>
          <span
            ref={bubbleRef}
            role="tooltip"
            className={styles.tooltip}
            style={position.style}
            data-state={presence.state}
            data-side={position.side}
            data-instant={instant}
            data-motion="fade"
            onAnimationEnd={presence.onAnimationEnd}
          >
            {content}
          </span>
        </Layer>
      ) : null}
    </>
  )
}
