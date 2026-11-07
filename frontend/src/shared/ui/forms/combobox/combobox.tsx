import { clsx } from "clsx"
import { type ChangeEvent, type KeyboardEvent, useId, useMemo, useRef, useState } from "react"
import { useTranslation } from "../../../i18n"
import { useLoadingIndicator } from "../../../motion"
import { Popover } from "../../overlays/popover/popover"
import type { IconName } from "../../primitives/icon/icon"
import { Spinner } from "../../states/spinner/spinner"
import { OptionList, type OptionSection } from "../option-list/option-list"
import { TextField } from "../text-field/text-field"
import styles from "./combobox.module.css"
import { useDebounced } from "./use-debounced"

export interface ComboboxItem {
  readonly value: string
  readonly label: string
  readonly icon?: IconName | undefined
  readonly meta?: string | undefined
}

export interface ComboboxGroup {
  readonly key: string
  readonly label: string
  readonly items: readonly ComboboxItem[]
}

export interface ComboboxProps {
  readonly label: string
  readonly groups: readonly ComboboxGroup[]
  readonly onQuery: (query: string) => void
  readonly onSelect: (item: ComboboxItem) => void
  readonly loading?: boolean
  readonly placeholder?: string | undefined
  readonly emptyText?: string | undefined
  readonly hideLabel?: boolean
  readonly minLength?: number
  readonly className?: string | undefined
}

function toSections(groups: readonly ComboboxGroup[]): OptionSection[] {
  return groups.map((group) => ({
    key: group.key,
    label: group.label,
    options: group.items.map((item) => ({ ...item, key: item.value })),
  }))
}

export function Combobox({
  label,
  groups,
  onQuery,
  onSelect,
  loading = false,
  placeholder,
  emptyText,
  hideLabel = false,
  minLength = 1,
  className,
}: ComboboxProps) {
  const { t } = useTranslation()
  const baseId = useId()
  const listId = `${baseId}list`
  const boxRef = useRef<HTMLDivElement | null>(null)
  const [query, setQuery] = useState("")
  const [open, setOpen] = useState(false)
  const [waiting, setWaiting] = useState(false)
  const [activeKey, setActiveKey] = useState<string | null>(null)
  const items = useMemo(() => groups.flatMap((group) => group.items), [groups])
  const sections = useMemo(() => toSections(groups), [groups])
  const searching = loading || waiting
  const indicator = useLoadingIndicator({ pending: searching, hasData: items.length > 0 })
  const sendQuery = useDebounced((next: string) => {
    setWaiting(false)
    onQuery(next)
  })

  const active = items.find((item) => item.value === activeKey)
  const indexOf = (key: string) => items.findIndex((item) => item.value === key)
  const optionId = (key: string) => `${baseId}option${indexOf(key)}`
  const spinning = searching && (indicator === "spinner" || indicator === "skeleton")
  const empty = !searching && items.length === 0
  const shown = open && query.trim().length >= minLength && (items.length > 0 || spinning || empty)

  const search = (next: string) => {
    setQuery(next)
    setActiveKey(null)
    setWaiting(true)
    sendQuery(next)
  }

  const pick = (item: ComboboxItem) => {
    setQuery(item.label)
    setOpen(false)
    setActiveKey(null)
    onSelect(item)
  }

  const move = (delta: 1 | -1) => {
    setOpen(true)
    const last = items.length - 1
    if (last < 0) return
    const current = active === undefined ? -1 : items.indexOf(active)
    const next = current < 0 ? (delta > 0 ? 0 : last) : Math.min(Math.max(current + delta, 0), last)
    setActiveKey(items[next]?.value ?? null)
  }

  const onEnter = (event: KeyboardEvent<HTMLInputElement>) => {
    if (!shown || active === undefined) return
    event.preventDefault()
    pick(active)
  }

  const onEscape = (event: KeyboardEvent<HTMLInputElement>) => {
    if (query === "") return
    event.preventDefault()
    event.stopPropagation()
    search("")
  }

  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault()
      move(event.key === "ArrowDown" ? 1 : -1)
    }
    if (event.key === "Enter") onEnter(event)
    if (event.key === "Escape") onEscape(event)
  }

  const footer = spinning ? (
    <div className={styles.row}>
      <Spinner label={t("common:ui.combobox.loading")} />
    </div>
  ) : empty ? (
    <p className={styles.row} role="status">
      {emptyText ?? t("common:ui.combobox.empty")}
    </p>
  ) : null

  return (
    <div className={clsx(styles.combobox, className)}>
      <TextField
        label={label}
        hideLabel={hideLabel}
        icon="search"
        boxRef={boxRef}
        value={query}
        placeholder={placeholder}
        autoComplete="off"
        role="combobox"
        aria-autocomplete="list"
        aria-expanded={shown}
        aria-controls={shown && items.length > 0 ? listId : undefined}
        aria-activedescendant={shown && active !== undefined ? optionId(active.value) : undefined}
        onChange={(event: ChangeEvent<HTMLInputElement>) => {
          setOpen(true)
          search(event.currentTarget.value)
        }}
        onKeyDown={onKeyDown}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
      />
      <Popover open={shown} onClose={() => setOpen(false)} anchorRef={boxRef} matchWidth>
        <OptionList
          id={listId}
          label={label}
          sections={sections}
          activeKey={activeKey}
          selectedKey={activeKey}
          optionId={optionId}
          stale={searching && indicator !== "none" && items.length > 0}
          onActivate={setActiveKey}
          onPick={(key) => {
            const item = items[indexOf(key)]
            if (item !== undefined) pick(item)
          }}
          footer={footer}
        />
      </Popover>
    </div>
  )
}
