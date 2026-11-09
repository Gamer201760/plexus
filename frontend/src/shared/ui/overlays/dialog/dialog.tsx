import type { ReactNode } from "react"
import { Modal } from "../modal/modal"
import styles from "./dialog.module.css"

export interface DialogProps {
  readonly open: boolean
  readonly onClose: () => void
  readonly title: string
  readonly description?: string | undefined
  readonly actions?: ReactNode
  readonly children?: ReactNode
}

export function Dialog(props: DialogProps) {
  return <Modal {...props} frameClassName={styles.frame} panelClassName={styles.dialog} />
}
