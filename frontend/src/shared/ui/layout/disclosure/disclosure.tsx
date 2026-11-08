import { type ReactNode, useId, useState } from "react"
import { useInputModality, usePresence } from "../../../motion"
import { Icon } from "../../primitives/icon/icon"
import styles from "./disclosure.module.css"

export interface DisclosureProps {
  readonly title: ReactNode
  readonly children: ReactNode
  readonly defaultOpen?: boolean
  readonly className?: string | undefined
}
export function Disclosure({ title, children, defaultOpen = false, className }: DisclosureProps) {
  const [open, setOpen] = useState(defaultOpen)
  const id = useId()
  const modality = useInputModality()
  const presence = usePresence(open, "--dur-fast-exit", modality.instant)
  return (
    <div className={className}>
      <button
        type="button"
        className={styles.trigger}
        aria-expanded={open}
        aria-controls={id}
        onKeyDown={modality.onKeyDown}
        onPointerDown={modality.onPointerDown}
        onClick={() => setOpen(!open)}
      >
        <Icon name="chevron-down" size="sm" />
        <span>{title}</span>
      </button>
      <div
        id={id}
        hidden={!presence.mounted}
        inert={!open}
        className={styles.content}
        data-state={presence.state}
        data-instant={modality.instant}
        onTransitionEnd={presence.onTransitionEnd}
      >
        {children}
      </div>
    </div>
  )
}
