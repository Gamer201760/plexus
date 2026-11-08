import { describe, expect, it } from "vitest"
import { flightPath, type MapView } from "@/entities/region/russia-map/map-motion"

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
