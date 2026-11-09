import { clsx } from "clsx"
import { type MouseEvent, type ReactNode, useEffect, useId, useRef } from "react"
import { ScrollArea } from "../../layout/scroll-area/scroll-area"
import { Icon, type IconName } from "../../primitives/icon/icon"
import styles from "./option-list.module.css"

export interface OptionEntry {
  readonly key: string
  readonly label: string
  readonly icon?: IconName | undefined
  readonly meta?: string | undefined
}

export interface OptionSection {
  readonly key: string
  readonly label?: string | undefined
  readonly options: readonly OptionEntry[]
}

export interface OptionListProps {
  readonly id: string
  readonly label: string
  readonly sections: readonly OptionSection[]
  readonly activeKey: string | null
  readonly selectedKey: string | null
  readonly optionId: (key: string) => string
  readonly onActivate: (key: string) => void
  readonly onPick: (key: string) => void
  readonly stale?: boolean
  readonly footer?: ReactNode
}

interface RowProps {
  readonly entry: OptionEntry
  readonly id: string
  readonly active: boolean
  readonly selected: boolean
  readonly onActivate: (key: string) => void
  readonly onPick: (key: string) => void
}

function OptionRow({ entry, id, active, selected, onActivate, onPick }: RowProps) {
  const ref = useRef<HTMLDivElement | null>(null)
  useEffect(() => {
    const element = ref.current
    if (active && element !== null && typeof element.scrollIntoView === "function")
      element.scrollIntoView({ block: "nearest" })
  }, [active])
  return (
    // biome-ignore lint/a11y/useKeyWithClickEvents: keys are handled by the owning combobox through aria-activedescendant
    <div
      ref={ref}
      id={id}
      role="option"
      aria-selected={selected}
      aria-labelledby={`${id}label`}
      aria-describedby={entry.meta === undefined ? undefined : `${id}meta`}
      tabIndex={-1}
      className={styles.option}
      data-active={active}
      onPointerMove={() => onActivate(entry.key)}
      onClick={() => onPick(entry.key)}
    >
      {entry.icon === undefined ? null : (
        <Icon name={entry.icon} size="sm" className={styles.icon} />
      )}
      <span id={`${id}label`} className={styles.label}>
        {entry.label}
      </span>
      {entry.meta === undefined ? null : (
        <span id={`${id}meta`} className={styles.meta}>
          {entry.meta}
        </span>
      )}
      <Icon name="check" size="sm" className={styles.check} />
    </div>
  )
}

interface SectionProps extends Omit<OptionListProps, "id" | "label" | "sections" | "footer"> {
  readonly section: OptionSection
}

function Section({ section, activeKey, selectedKey, optionId, ...handlers }: SectionProps) {
  const headingId = useId()
  const rows = section.options.map((entry) => (
    <OptionRow
      key={entry.key}
      entry={entry}
      id={optionId(entry.key)}
      active={entry.key === activeKey}
      selected={entry.key === selectedKey}
      {...handlers}
    />
  ))
  if (section.label === undefined) return rows
  return (
    // biome-ignore lint/a11y/useSemanticElements: a listbox only accepts role=group containers, fieldset would add form semantics
    <div role="group" aria-labelledby={headingId} className={styles.group}>
      <div id={headingId} role="presentation" className={styles.heading}>
        {section.label}
      </div>
      {rows}
    </div>
  )
}

const keepFocus = (event: MouseEvent<HTMLDivElement>) => event.preventDefault()

export function OptionList({
  id,
  label,
  sections,
  stale = false,
  footer,
  ...rest
}: OptionListProps) {
  const empty = sections.every((section) => section.options.length === 0)
  return (
    <ScrollArea className={styles.scroller} onMouseDown={keepFocus}>
      {empty ? null : (
        <div
          id={id}
          role="listbox"
          aria-label={label}
          className={clsx(styles.list, stale && styles.stale)}
        >
          {sections.map((section) => (
            <Section key={section.key} section={section} {...rest} />
          ))}
        </div>
      )}
      {footer}
    </ScrollArea>
  )
}
