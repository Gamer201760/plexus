import { clsx } from "clsx"
import { useTranslation } from "../../../i18n"
import { Icon } from "../../primitives/icon/icon"
import { Tooltip } from "../tooltip/tooltip"
import styles from "./close-button.module.css"

export interface CloseButtonProps {
  readonly onClick: () => void
  readonly label?: string | undefined
  readonly className?: string | undefined
}

export function CloseButton({ onClick, label, className }: CloseButtonProps) {
  const { t } = useTranslation()
  const text = label ?? t("common:ui.close")
  return (
    <Tooltip content={text} describe={false}>
      <button
        type="button"
        aria-label={text}
        className={clsx(styles.close, className)}
        onClick={onClick}
      >
        <Icon name="x" size="md" />
      </button>
    </Tooltip>
  )
}
