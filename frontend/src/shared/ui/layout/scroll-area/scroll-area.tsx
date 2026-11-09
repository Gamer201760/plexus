import { clsx } from "clsx"
import type { HTMLAttributes, ReactNode, Ref } from "react"
import styles from "./scroll-area.module.css"

export type ScrollOrientation = "vertical" | "horizontal" | "both"

export interface ScrollAreaProps extends Omit<HTMLAttributes<HTMLDivElement>, "children"> {
  readonly orientation?: ScrollOrientation
  readonly label?: string | undefined
  readonly ref?: Ref<HTMLDivElement> | undefined
  readonly children: ReactNode
}

const ORIENTATION_CLASS: Readonly<Record<ScrollOrientation, string | undefined>> = {
  vertical: styles.vertical,
  horizontal: styles.horizontal,
  both: styles.both,
}

export function ScrollArea({
  orientation = "vertical",
  label,
  className,
  children,
  ...rest
}: ScrollAreaProps) {
  const region = label === undefined || label === "" ? {} : { role: "region", "aria-label": label }
  return (
    <div
      {...region}
      tabIndex={label === undefined || label === "" ? undefined : 0}
      {...rest}
      className={clsx(styles.area, ORIENTATION_CLASS[orientation], className)}
      data-orientation={orientation}
    >
      {children}
    </div>
  )
}
