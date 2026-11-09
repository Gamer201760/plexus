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

export type DrawPhase = "settled" | "moving" | "flying"

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

export function visibleBox(view: MapView, frame: Box, size: Size): Box {
  const k = unitsPerPixel(frame, size)
  return {
    x: (frame.x - view.x - (size.width * k - frame.width) / 2) / view.scale,
    y: (frame.y - view.y - (size.height * k - frame.height) / 2) / view.scale,
    width: (size.width * k) / view.scale,
    height: (size.height * k) / view.scale,
  }
}

export interface FlightPath {
  readonly frames: readonly MapView[]
  readonly reach: number
}

const SAMPLES = 32
const ARC_DEPTH = 0.45

function easeInOut(t: number): number {
  return t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2
}

function centerOf(view: MapView, frame: Box): { x: number; y: number } {
  return {
    x: (frame.x + frame.width / 2 - view.x) / view.scale,
    y: (frame.y + frame.height / 2 - view.y) / view.scale,
  }
}

export function flightPath(from: MapView, to: MapView, frame: Box): FlightPath {
  const start = centerOf(from, frame)
  const end = centerOf(to, frame)
  const sight = frame.width / Math.max(from.scale, to.scale)
  const reach = Math.min(1, Math.hypot(end.x - start.x, end.y - start.y) / sight)
  const dip = ARC_DEPTH * Math.max(0, reach - 0.3)
  const frames: MapView[] = []
  for (let index = 0; index <= SAMPLES; index += 1) {
    const eased = easeInOut(index / SAMPLES)
    const logScale = Math.log(from.scale) + (Math.log(to.scale) - Math.log(from.scale)) * eased
    const scale = Math.max(1, Math.exp(logScale) * (1 - dip * Math.sin(Math.PI * eased)))
    const cx = start.x + (end.x - start.x) * eased
    const cy = start.y + (end.y - start.y) * eased
    frames.push({
      scale,
      x: frame.x + frame.width / 2 - cx * scale,
      y: frame.y + frame.height / 2 - cy * scale,
    })
  }
  return { frames, reach }
}
