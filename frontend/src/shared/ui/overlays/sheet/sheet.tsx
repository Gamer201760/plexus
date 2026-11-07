import { clsx } from "clsx"
import type { ReactNode } from "react"
import { Modal } from "../modal/modal"
import styles from "./sheet.module.css"

export type SheetPlacement = "responsive" | "bottom" | "side"

export interface SheetProps {
  readonly open: boolean
  readonly onClose: () => void
  readonly title: string
  readonly description?: string | undefined
  readonly placement?: SheetPlacement
  readonly actions?: ReactNode
  readonly children?: ReactNode
}

const PLACEMENT_CLASS: Readonly<Record<SheetPlacement, string | undefined>> = {
  responsive: styles.responsive,
  bottom: styles.bottom,
  side: styles.side,
}

export function Sheet({ placement = "responsive", ...rest }: SheetProps) {
  const placementClass = PLACEMENT_CLASS[placement]
  return (
    <Modal
      {...rest}
      frameClassName={clsx(styles.frame, placementClass)}
      panelClassName={clsx(styles.sheet, placementClass)}
    />
  )
}
