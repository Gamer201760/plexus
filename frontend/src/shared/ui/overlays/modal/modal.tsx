import { clsx } from "clsx"
import { type KeyboardEvent, type ReactNode, useId, useRef } from "react"
import { usePresence } from "../../../motion"
import { ScrollArea } from "../../layout/scroll-area/scroll-area"
import { CloseButton } from "../close-button/close-button"
import { Layer, LayerHost } from "../layer-host/layer-host"
import styles from "./modal.module.css"
import { trapTab, useModalFocus } from "./use-modal-focus"

export interface ModalProps {
  readonly open: boolean
  readonly onClose: () => void
  readonly title: string
  readonly description?: string | undefined
  readonly actions?: ReactNode
  readonly children?: ReactNode
  readonly frameClassName?: string | undefined
  readonly panelClassName?: string | undefined
}

export function Modal({
  open,
  onClose,
  title,
  description,
  actions,
  children,
  frameClassName,
  panelClassName,
}: ModalProps) {
  const titleId = useId()
  const descriptionId = useId()
  const rootRef = useRef<HTMLDivElement | null>(null)
  const titleRef = useRef<HTMLHeadingElement | null>(null)
  const presence = usePresence(open)
  useModalFocus(open, titleRef)

  const onKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key === "Escape" && open) {
      event.stopPropagation()
      onClose()
      return
    }
    if (rootRef.current !== null) trapTab(event, rootRef.current)
  }

  if (!presence.mounted) return null
  return (
    <Layer>
      <div ref={rootRef} className={clsx(styles.root, frameClassName)} data-state={presence.state}>
        <div
          className={styles.backdrop}
          aria-hidden="true"
          data-motion="fade"
          onPointerDown={onClose}
        />
        <LayerHost>
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            aria-describedby={description === undefined ? undefined : descriptionId}
            className={clsx(styles.panel, panelClassName)}
            data-state={presence.state}
            data-motion="fade"
            onAnimationEnd={presence.onAnimationEnd}
            onKeyDown={onKeyDown}
          >
            <header className={styles.header}>
              <h2 id={titleId} ref={titleRef} tabIndex={-1} className={styles.title}>
                {title}
              </h2>
              <CloseButton onClick={onClose} />
            </header>
            {description === undefined ? null : (
              <p id={descriptionId} className={styles.description}>
                {description}
              </p>
            )}
            {children === undefined ? null : (
              <ScrollArea label={title} className={styles.body}>
                {children}
              </ScrollArea>
            )}
            {actions === undefined ? null : <footer className={styles.actions}>{actions}</footer>}
          </section>
        </LayerHost>
      </div>
    </Layer>
  )
}
