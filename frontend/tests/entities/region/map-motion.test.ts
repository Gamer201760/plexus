import { describe, expect, it } from "vitest"
import {
  flightPath,
  type MapView,
  unitsPerPixel,
  viewShift,
  visibleBox,
} from "@/entities/region/russia-map/map-motion"

const FRAME = { x: 0, y: 0, width: 1000, height: 600 }
const HOME: MapView = { scale: 1, x: 0, y: 0 }

describe("flightPath", () => {
  it("starts at the current view and lands on the target", () => {
    const target: MapView = { scale: 4, x: -1200, y: -400 }
    const { frames } = flightPath(HOME, target, FRAME)
    expect(frames[0]).toEqual(HOME)
    const last = frames[frames.length - 1]
    expect(last?.scale).toBeCloseTo(4)
    expect(last?.x).toBeCloseTo(-1200)
    expect(last?.y).toBeCloseTo(-400)
  })

  it("pulls the camera back between distant regions", () => {
    const west: MapView = { scale: 5, x: -500, y: -1000 }
    const east: MapView = { scale: 5, x: -4000, y: -1000 }
    const { frames, reach } = flightPath(west, east, FRAME)
    expect(reach).toBe(1)
    expect(Math.min(...frames.map((view) => view.scale))).toBeLessThan(5)
  })

  it("keeps the scale while panning to a neighbour", () => {
    const here: MapView = { scale: 5, x: -2000, y: -1000 }
    const near: MapView = { scale: 5, x: -2100, y: -1000 }
    const { frames } = flightPath(here, near, FRAME)
    for (const view of frames) expect(view.scale).toBeCloseTo(5)
  })
})

describe("viewShift", () => {
  const size = { width: 800, height: 700 }
  const k = unitsPerPixel(FRAME, size)
  const padX = (size.width - FRAME.width / k) / 2
  const padY = (size.height - FRAME.height / k) / 2
  const screen = (view: MapView, x: number, y: number) => ({
    x: padX + (view.x + view.scale * x - FRAME.x) / k,
    y: padY + (view.y + view.scale * y - FRAME.y) / k,
  })
  const parse = (transform: string) => {
    const match = /translate\((.+)px, (.+)px\) scale\((.+)\)/.exec(transform)
    return (match?.slice(1) ?? []).map(Number)
  }

  it("moves a rendering made for one view onto another view", () => {
    const base: MapView = { scale: 2, x: -300, y: -100 }
    const view: MapView = { scale: 3.5, x: -900, y: -420 }
    const [tx = 0, ty = 0, ratio = 0] = parse(viewShift(base, view, FRAME, size))
    for (const [x, y] of [
      [100, 50],
      [420, 300],
    ] as const) {
      const from = screen(base, x, y)
      const to = screen(view, x, y)
      expect(tx + ratio * from.x).toBeCloseTo(to.x)
      expect(ty + ratio * from.y).toBeCloseTo(to.y)
    }
  })

  it("is the identity for an unchanged view", () => {
    const view: MapView = { scale: 4, x: -1200, y: -500 }
    expect(parse(viewShift(view, view, FRAME, size))).toEqual([0, 0, 1])
  })

  it("covers the whole frame at the home view", () => {
    const box = visibleBox(HOME, FRAME, size)
    expect(box.x).toBeLessThanOrEqual(FRAME.x)
    expect(box.y).toBeLessThanOrEqual(FRAME.y)
    expect(box.x + box.width).toBeGreaterThanOrEqual(FRAME.x + FRAME.width)
    expect(box.y + box.height).toBeGreaterThanOrEqual(FRAME.y + FRAME.height)
  })
})
