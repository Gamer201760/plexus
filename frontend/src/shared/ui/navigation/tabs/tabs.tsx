import { clsx } from "clsx"
import { type KeyboardEvent, type ReactNode, useId, useRef } from "react"
import { useInputModality, useSlidingIndicator } from "../../../motion"
import { useContentFade } from "../../../motion/use-content-fade"
import { ScrollArea } from "../../layout/scroll-area/scroll-area"
import { Icon, type IconName } from "../../primitives/icon/icon"
import styles from "./tabs.module.css"

export interface TabItem<T extends string> {
  readonly value: T
  readonly label: string
  readonly icon?: IconName | undefined
}

export interface TabsProps<T extends string> {
  readonly label: string
  readonly items: readonly TabItem<T>[]
  readonly value: T
  readonly onChange: (value: T) => void
  readonly children?: ReactNode
  readonly className?: string | undefined
}

const MOVES: Readonly<Record<string, (index: number, count: number) => number>> = {
  ArrowRight: (index, count) => (index + 1) % count,
  ArrowLeft: (index, count) => (index - 1 + count) % count,
  Home: () => 0,
  End: (_index, count) => count - 1,
}

export function Tabs<T extends string>({
  label,
  items,
  value,
  onChange,
  children,
  className,
}: TabsProps<T>) {
  const baseId = useId()
  const panelId = `${baseId}panel`
  const tabId = (item: T) => `${baseId}tab${items.findIndex((entry) => entry.value === item)}`
  const modality = useInputModality()
  const panelRef = useRef<HTMLDivElement>(null)
  useContentFade(panelRef, value, modality.instant)
  const { listRef, indicatorRef, itemRef } = useSlidingIndicator<HTMLDivElement>(value, {
    instant: modality.instant,
    radiusToken: "--radius-xs",
  })

  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    modality.onKeyDown()
    const move = MOVES[event.key]
    const current = items.findIndex((item) => item.value === value)
    if (move === undefined || items.length === 0) return
    event.preventDefault()
    const next = items[move(current, items.length)]
    if (next === undefined) return
    onChange(next.value)
    document.getElementById(tabId(next.value))?.focus()
  }

  return (
    <div className={clsx(styles.tabs, className)}>
      <ScrollArea orientation="horizontal" className={styles.scroller}>
        <div
          ref={listRef}
          role="tablist"
          aria-label={label}
          className={styles.list}
          onKeyDown={onKeyDown}
          onPointerDown={modality.onPointerDown}
        >
          <span ref={indicatorRef} className={styles.indicator} aria-hidden="true" />
          {items.map((item) => {
            const selected = item.value === value
            return (
              <button
                key={item.value}
                ref={itemRef(item.value)}
                id={tabId(item.value)}
                type="button"
                role="tab"
                aria-selected={selected}
                aria-controls={children === undefined ? undefined : panelId}
                tabIndex={selected ? 0 : -1}
                className={styles.tab}
                onClick={() => onChange(item.value)}
              >
                {item.icon === undefined ? null : <Icon name={item.icon} size="md" />}
                <span>{item.label}</span>
              </button>
            )
          })}
        </div>
      </ScrollArea>
      {children === undefined ? null : (
        <div
          ref={panelRef}
          id={panelId}
          role="tabpanel"
          aria-labelledby={tabId(value)}
          className={styles.panel}
        >
          {children}
        </div>
      )}
    </div>
  )
}
