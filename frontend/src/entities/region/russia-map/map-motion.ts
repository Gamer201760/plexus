export interface MapView {
  readonly scale: number
  readonly x: number
  readonly y: number
}

export interface Box {
  readonly x: number
  readonly y: number
  readonly width: number
  readonly height: number
}

export interface Size {
  readonly width: number
  readonly height: number
}

export function unitsPerPixel(frame: Box, size: Size): number {
  if (size.width === 0 || size.height === 0) return 1
  return Math.max(frame.width / size.width, frame.height / size.height)
}

export function viewShift(from: MapView, to: MapView, frame: Box, size: Size): string {
  const k = unitsPerPixel(frame, size)
  const ratio = to.scale / from.scale
  const padX = (size.width - frame.width / k) / 2
  const padY = (size.height - frame.height / k) / 2
  const shiftX = padX * (1 - ratio) + (ratio * (frame.x - from.x) + to.x - frame.x) / k
  const shiftY = padY * (1 - ratio) + (ratio * (frame.y - from.y) + to.y - frame.y) / k
  return `translate(${shiftX}px, ${shiftY}px) scale(${ratio})`
}

export function composeTransforms(outer: string, inner: string): string {
  return outer === "none" || outer === "" ? inner : `${outer} ${inner}`
}
