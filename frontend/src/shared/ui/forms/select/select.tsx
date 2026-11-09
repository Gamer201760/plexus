import { clsx } from "clsx"
import { type KeyboardEvent, useId, useMemo, useRef } from "react"
import { useTranslation } from "../../../i18n"
import { Popover } from "../../overlays/popover/popover"
import { Icon, type IconName } from "../../primitives/icon/icon"
import { OptionList } from "../option-list/option-list"
import styles from "./select.module.css"
import { useSelectController } from "./use-select"

export interface SelectOption<T extends string> {
  readonly value: T
  readonly label: string
  readonly icon?: IconName | undefined
  readonly meta?: string | undefined
}

export interface SelectProps<T extends string> {
  readonly label: string
  readonly options: readonly SelectOption<T>[]
  readonly value: T | null
  readonly onChange: (value: T) => void
  readonly hideLabel?: boolean
  readonly placeholder?: string | undefined
  readonly disabled?: boolean
  readonly className?: string | undefined
}

const stopSpaceClick = (event: KeyboardEvent<HTMLButtonElement>) => {
  if (event.key === " ") event.preventDefault()
}

export function Select<T extends string>({
  label,
  options,
  value,
  onChange,
  hideLabel = false,
  placeholder,
  disabled = false,
  className,
}: SelectProps<T>) {
  const { t } = useTranslation()
  const baseId = useId()
  const labelId = `${baseId}label`
  const listId = `${baseId}list`
  const triggerRef = useRef<HTMLButtonElement | null>(null)
  const labels = useMemo(() => options.map((option) => option.label), [options])
  const indexOf = (key: string) => options.findIndex((option) => option.value === key)
  const optionId = (key: string) => `${baseId}option${indexOf(key)}`
  const selectedIndex = value === null ? -1 : indexOf(value)
  const controller = useSelectController(labels, selectedIndex, (index) => {
    const option = options[index]
    if (option !== undefined) onChange(option.value)
  })
  const selected = options[selectedIndex]
  const active = controller.open ? options[controller.activeIndex] : undefined

  return (
    <div className={clsx(styles.select, className)}>
      <span id={labelId} className={hideLabel ? "visually-hidden" : styles.label}>
        {label}
      </span>
      <button
        ref={triggerRef}
        type="button"
        role="combobox"
        aria-labelledby={labelId}
        aria-haspopup="listbox"
        aria-expanded={controller.open}
        aria-controls={controller.open ? listId : undefined}
        aria-activedescendant={active === undefined ? undefined : optionId(active.value)}
        disabled={disabled}
        className={styles.trigger}
        onClick={controller.toggle}
        onKeyDown={controller.onKeyDown}
        onKeyUp={stopSpaceClick}
      >
        {selected?.icon === undefined ? null : (
          <Icon name={selected.icon} size="sm" className={styles.muted} />
        )}
        <span className={clsx(styles.value, selected === undefined && styles.placeholder)}>
          {selected?.label ?? placeholder ?? t("common:ui.select.placeholder")}
        </span>
        <Icon name="chevron-down" size="sm" className={styles.chevron} />
      </button>
      <Popover open={controller.open} onClose={controller.close} anchorRef={triggerRef} matchWidth>
        <OptionList
          id={listId}
          label={label}
          sections={[
            { key: listId, options: options.map((option) => ({ ...option, key: option.value })) },
          ]}
          activeKey={active?.value ?? null}
          selectedKey={value}
          optionId={optionId}
          onActivate={(key) => controller.setActiveIndex(indexOf(key))}
          onPick={(key) => controller.pick(indexOf(key))}
        />
      </Popover>
    </div>
  )
}
