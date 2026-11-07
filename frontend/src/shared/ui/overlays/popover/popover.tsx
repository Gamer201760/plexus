import { clsx } from "clsx"
import { type ReactNode, type RefObject, useRef } from "react"
import { usePresence } from "../../../motion"
import { Layer } from "../layer-host/layer-host"
import type { PopoverAlign, PopoverSide } from "./anchored-position"
import styles from "./popover.module.css"
import { useAnchoredPosition } from "./use-anchored-position"
import { useDismiss } from "./use-dismiss"

export type { PopoverAlign, PopoverSide } from "./anchored-position"

export interface PopoverProps {
  readonly open: boolean
  readonly onClose: () => void
  readonly anchorRef: RefObject<HTMLElement | null>
  readonly side?: PopoverSide
  readonly align?: PopoverAlign
  readonly matchWidth?: boolean
  readonly focusOnOpen?: boolean
  readonly id?: string | undefined
  readonly label?: string | undefined
  readonly className?: string | undefined
  readonly children: ReactNode
}

export function Popover({
  open,
  onClose,
  anchorRef,
  side = "bottom",
  align = "start",
  matchWidth = false,
  focusOnOpen = false,
  id,
  label,
  className,
  children,
}: PopoverProps) {
  const presence = usePresence(open)
  const floatingRef = useRef<HTMLDivElement | null>(null)
  const position = useAnchoredPosition(anchorRef, floatingRef, {
    active: presence.mounted,
    side,
    align,
    matchWidth,
  })
  useDismiss({ open, onClose, anchorRef, floatingRef, focusOnOpen })

  if (!presence.mounted) return null
  return (
    <Layer>
      <div
        ref={floatingRef}
        id={id}
        {...(label === undefined ? {} : { role: "dialog", "aria-label": label })}
        tabIndex={focusOnOpen ? -1 : undefined}
        className={clsx(styles.popover, className)}
        style={position.style}
        data-state={presence.state}
        data-side={position.side}
        data-align={align}
        data-motion="fade"
        onAnimationEnd={presence.onAnimationEnd}
      >
        {children}
      </div>
    </Layer>
  )
}
