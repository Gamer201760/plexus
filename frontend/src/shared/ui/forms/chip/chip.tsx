import { clsx } from "clsx"
import type { ReactNode } from "react"
import { Icon, type IconName } from "../../primitives/icon/icon"
import styles from "./chip.module.css"

export interface ChipProps {
  readonly pressed: boolean
  readonly onPressedChange: (pressed: boolean) => void
  readonly icon?: IconName | undefined
  readonly disabled?: boolean
  readonly className?: string | undefined
  readonly children: ReactNode
}

export function Chip({
  pressed,
  onPressedChange,
  icon,
  disabled = false,
  className,
  children,
}: ChipProps) {
  return (
    <button
      type="button"
      aria-pressed={pressed}
      disabled={disabled}
      className={clsx(styles.chip, className)}
      onClick={() => onPressedChange(!pressed)}
    >
      <span className={styles.content}>
        {icon === undefined ? null : <Icon name={icon} size="sm" />}
        <span>{children}</span>
      </span>
    </button>
  )
}

export interface ChipOption<T extends string> {
  readonly value: T
  readonly label: string
  readonly icon?: IconName | undefined
}

export interface ChipGroupProps<T extends string> {
  readonly label: string
  readonly options: readonly ChipOption<T>[]
  readonly value: readonly T[]
  readonly onChange: (value: T[]) => void
  readonly className?: string | undefined
}

export function ChipGroup<T extends string>({
  label,
  options,
  value,
  onChange,
  className,
}: ChipGroupProps<T>) {
  const toggle = (option: T, pressed: boolean) =>
    onChange(
      pressed
        ? options
            .map((item) => item.value)
            .filter((item) => item === option || value.includes(item))
        : value.filter((item) => item !== option),
    )
  return (
    <fieldset className={clsx(styles.group, className)}>
      <legend className="visually-hidden">{label}</legend>
      {options.map((option) => (
        <Chip
          key={option.value}
          icon={option.icon}
          pressed={value.includes(option.value)}
          onPressedChange={(pressed) => toggle(option.value, pressed)}
        >
          {option.label}
        </Chip>
      ))}
    </fieldset>
  )
}
