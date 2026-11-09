import { createContext, type ReactNode, useContext, useState } from "react"
import { createPortal } from "react-dom"
import styles from "./layer-host.module.css"

const LayerContext = createContext<HTMLElement | null>(null)

export interface LayerHostProps {
  readonly children: ReactNode
}

export function LayerHost({ children }: LayerHostProps) {
  const parent = useContext(LayerContext)
  const [host, setHost] = useState<HTMLElement | null>(null)
  return (
    <LayerContext value={host ?? parent}>
      {children}
      <div ref={setHost} className={styles.host} data-layer-host="" />
    </LayerContext>
  )
}

export interface LayerProps {
  readonly children: ReactNode
}

export function Layer({ children }: LayerProps) {
  const host = useContext(LayerContext)
  const target = host ?? (typeof document === "undefined" ? null : document.body)
  return target === null ? null : createPortal(children, target)
}
