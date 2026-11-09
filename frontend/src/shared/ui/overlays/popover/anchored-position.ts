export type PopoverSide = "top" | "bottom"
export type PopoverAlign = "start" | "center" | "end"

export interface Box {
  readonly top: number
  readonly left: number
  readonly width: number
  readonly height: number
}

export interface Size {
  readonly width: number
  readonly height: number
}

export interface PlacementInput {
  readonly anchor: Box
  readonly floating: Size
  readonly viewport: Size
  readonly gap: number
  readonly margin: number
  readonly side: PopoverSide
  readonly align: PopoverAlign
  readonly matchWidth: boolean
}

export interface Placement {
  readonly side: PopoverSide
  readonly top: number
  readonly left: number
  readonly maxHeight: number
  readonly maxWidth: number
  readonly minWidth: number | null
}

function chooseSide(preferred: PopoverSide, height: number, below: number, above: number) {
  if (preferred === "bottom") return height <= below || below >= above ? "bottom" : "top"
  return height <= above || above >= below ? "top" : "bottom"
}

function alignedLeft(anchor: Box, width: number, align: PopoverAlign): number {
  if (align === "start") return anchor.left
  if (align === "end") return anchor.left + anchor.width - width
  return anchor.left + (anchor.width - width) / 2
}

export function placeFloating(input: PlacementInput): Placement {
  const { anchor, floating, viewport, gap, margin } = input
  const below = viewport.height - (anchor.top + anchor.height) - gap - margin
  const above = anchor.top - gap - margin
  const side = chooseSide(input.side, floating.height, below, above)
  const maxHeight = Math.max(0, side === "bottom" ? below : above)
  const height = Math.min(floating.height, maxHeight)
  const top = side === "bottom" ? anchor.top + anchor.height + gap : anchor.top - gap - height
  const width = input.matchWidth ? Math.max(floating.width, anchor.width) : floating.width
  const highest = viewport.width - margin - width
  const left = Math.max(margin, Math.min(alignedLeft(anchor, width, input.align), highest))
  const maxWidth = Math.max(0, viewport.width - margin * 2)
  return { side, top, left, maxHeight, maxWidth, minWidth: input.matchWidth ? anchor.width : null }
}
