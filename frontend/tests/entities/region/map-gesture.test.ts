import { describe, expect, it } from "vitest"
import {
  constrainView,
  HOME,
  localPoint,
  wheelPixels,
  zoomAt,
} from "@/entities/region/russia-map/map-gesture"

const frame = { x: 0, y: 0, width: 1000, height: 620 }

describe("map gestures", () => {
  it("preserves the point under the cursor while zooming", () => {
    const point = { x: 400, y: 300 }
    const view = { scale: 2, x: -200, y: -100 }
    const next = zoomAt(view, 1.8, point, frame)
    expect((point.x - next.x) / next.scale).toBeCloseTo((point.x - view.x) / view.scale)
    expect((point.y - next.y) / next.scale).toBeCloseTo((point.y - view.y) / view.scale)
  })
  it("limits zoom-out without forcing a camera reset", () => {
    expect(zoomAt({ scale: 4, x: -1700, y: -1000 }, 0.01, { x: 12, y: 15 }, frame).scale).toBe(1)
  })
  it("keeps the map in the viewport at both pan boundaries", () => {
    expect(constrainView({ scale: 2, x: 5000, y: -5000 }, frame)).toEqual({
      scale: 2,
      x: 850,
      y: -1147,
    })
  })
  it("accounts for letterboxing and page offset", () => {
    expect(
      localPoint({ x: 600, y: 520 }, frame, { left: 100, top: 20, width: 1000, height: 1000 }),
    ).toEqual({ x: 500, y: 310 })
  })
  it("normalizes pixel, line and page wheel deltas", () => {
    expect(wheelPixels(16, 0, 600)).toBe(wheelPixels(1, 1, 600))
    expect(wheelPixels(1, 2, 600)).toBe(600)
    expect(wheelPixels(0, 0, 600)).toBe(0)
  })
  it("caps extreme zoom without losing a finite view", () => {
    expect(zoomAt(HOME, 1e12, { x: 500, y: 310 }, frame)).toEqual({ scale: 12, x: -5500, y: -3410 })
  })
})

it("allows panning in every direction at the initial scale", () => {
  for (const sign of [-1, 1]) {
    const view = { scale: 1, x: sign * 140, y: sign * 70 }
    expect(constrainView(view, frame)).toEqual(view)
  }
})
