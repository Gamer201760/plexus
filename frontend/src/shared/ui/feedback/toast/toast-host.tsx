import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
} from "react"
import { useTranslation } from "../../../i18n"
import { Layer } from "../../overlays/layer-host/layer-host"
import { Toast, type ToastInput, type ToastRecord } from "./toast"
import styles from "./toast.module.css"

export interface ToastApi {
  readonly notify: (toast: ToastInput) => number
  readonly dismiss: (id: number) => void
}

const ToastContext = createContext<ToastApi | null>(null)

export function useToast(): ToastApi {
  const api = useContext(ToastContext)
  if (api === null) throw new Error("useToast must be used inside ToastHost")
  return api
}

export interface ToastHostProps {
  readonly children: ReactNode
}

export function ToastHost({ children }: ToastHostProps) {
  const { t } = useTranslation()
  const [toasts, setToasts] = useState<readonly ToastRecord[]>([])
  const [hovered, setHovered] = useState(false)
  const [focused, setFocused] = useState(false)
  const lastId = useRef(0)

  const notify = useCallback((toast: ToastInput) => {
    lastId.current += 1
    const id = lastId.current
    setToasts((list) => [...list, { ...toast, id, open: true }])
    return id
  }, [])
  const dismiss = useCallback((id: number) => {
    setToasts((list) => list.map((item) => (item.id === id ? { ...item, open: false } : item)))
  }, [])
  const remove = useCallback((id: number) => {
    setToasts((list) => list.filter((item) => item.id !== id))
  }, [])
  const api = useMemo(() => ({ notify, dismiss }), [notify, dismiss])

  return (
    <ToastContext value={api}>
      {children}
      <Layer>
        <section
          aria-label={t("common:ui.toast.region")}
          className={styles.region}
          onPointerEnter={() => setHovered(true)}
          onPointerLeave={() => setHovered(false)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
        >
          <ol className={styles.list} aria-live="polite">
            {toasts.map((toast) => (
              <Toast
                key={toast.id}
                toast={toast}
                paused={hovered || focused}
                onDismiss={dismiss}
                onRemoved={remove}
              />
            ))}
          </ol>
        </section>
      </Layer>
    </ToastContext>
  )
}
