import { Button } from "../../primitives/button/button"
import type { PopoverSide } from "../popover/anchored-position"
import { Tooltip } from "../tooltip/tooltip"

export interface HelpTipProps {
  readonly content: string
  readonly label: string
  readonly side?: PopoverSide
}

export function HelpTip({ content, label, side = "bottom" }: HelpTipProps) {
  return (
    <Tooltip content={content} side={side}>
      <Button variant="ghost" size="compact" icon="help" aria-label={label}>
        {null}
      </Button>
    </Tooltip>
  )
}
