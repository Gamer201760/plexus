import { clsx } from "clsx"
import { useEffect, useRef } from "react"
import { type DurationToken, motionMs, usePresence } from "../../../motion"
import { CloseButton } from "../../overlays/close-button/close-button"
import { Button } from "../../primitives/button/button"
import { Icon } from "../../primitives/icon/icon"
import { type StatusTone, TONE_CLASS, TONE_ICON } from "../status-badge/status-badge"
import styles from "./toast.module.css"

export interface ToastAction {
  readonly label: string
  readonly onClick: () => void
}

export interface ToastInput {
  readonly tone: StatusTone
  readonly title: string
  readonly description?: string | undefined
  readonly action?: ToastAction | undefined
}

export interface ToastRecord extends ToastInput {
  readonly id: number
  readonly open: boolean
}

function useAutoDismiss(running: boolean, token: DurationToken, onElapsed: () => void): void {
  const remaining = useRef<number | null>(null)
  const latest = useRef(onElapsed)
  latest.current = onElapsed

  useEffect(() => {
    if (!running) return
    const budget = remaining.current ?? motionMs(token)
    const started = performance.now()
    const timer = window.setTimeout(() => latest.current(), budget)
    return () => {
      window.clearTimeout(timer)
      remaining.current = Math.max(0, budget - (performance.now() - started))
    }
  }, [running, token])
}

export interface ToastProps {
  readonly toast: ToastRecord
  readonly paused: boolean
  readonly onDismiss: (id: number) => void
  readonly onRemoved: (id: number) => void
}

export function Toast({ toast, paused, onDismiss, onRemoved }: ToastProps) {
  const presence = usePresence(toast.open)
  const danger = toast.tone === "danger"
  useAutoDismiss(toast.open && !paused, danger ? "--delay-toast-error" : "--delay-toast", () =>
    onDismiss(toast.id),
  )
  useEffect(() => {
    if (!presence.mounted) onRemoved(toast.id)
  }, [presence.mounted, onRemoved, toast.id])

  if (!presence.mounted) return null
  return (
    <li
      className={clsx(styles.toast, TONE_CLASS[toast.tone])}
      role={danger ? "alert" : undefined}
      data-state={presence.state}
      data-tone={toast.tone}
      data-motion="fade"
      onAnimationEnd={presence.onAnimationEnd}
    >
      <Icon name={TONE_ICON[toast.tone]} size="md" className={styles.icon} />
      <div className={styles.text}>
        <p className={styles.title}>{toast.title}</p>
        {toast.description === undefined ? null : (
          <p className={styles.description}>{toast.description}</p>
        )}
      </div>
      <div className={styles.actions}>
        {toast.action === undefined ? null : (
          <Button variant="ghost" size="compact" onClick={toast.action.onClick}>
            {toast.action.label}
          </Button>
        )}
        <CloseButton onClick={() => onDismiss(toast.id)} />
      </div>
    </li>
  )
}
