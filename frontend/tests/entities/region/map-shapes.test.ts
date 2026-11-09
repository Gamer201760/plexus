import { readFileSync } from "node:fs"
import { describe, expect, it } from "vitest"
import {
  contains,
  encloses,
  expand,
  intersects,
  mainlandBox,
  union,
} from "@/entities/region/russia-map/map-shapes"

describe("map focus geometry", () => {
  it("focuses on the largest polygon without moving remote islands", () => {
    expect(mainlandBox("M0,0L100,0L100,100L0,100ZM500,500L510,500L510,510Z")).toEqual({
      x: 0,
      y: 0,
      width: 100,
      height: 100,
    })
  })
  it("uses area rather than coastline point count", () => {
    expect(mainlandBox("M0,0L20,0L0,20ZM80,80L81,80L82,80L82,81L81,81L80,81Z")?.x).toBe(0)
  })
  it("keeps Arkhangelsk mainland separate from the arctic islands", () => {
    const document = JSON.parse(readFileSync("atlas/public/geo/region-paths.json", "utf8"))
    const region = document.regions.find((entry: { id: string }) => entry.id === "11000000")
    const box = mainlandBox(region.path)
    expect(box?.y).toBeGreaterThan(180)
    expect(box?.width).toBeLessThan(120)
  })
  it("handles empty shapes and inclusive hit-test boundaries", () => {
    expect(mainlandBox("")).toBeNull()
    const box = { x: 0, y: 0, width: 10, height: 10 }
    expect(contains(box, 10, 10)).toBe(true)
    expect(contains(box, 11, 10)).toBe(false)
    expect(intersects(box, { x: 10, y: 2, width: 1, height: 1 })).toBe(true)
  })
})

describe("map cover boxes", () => {
  const box = { x: 10, y: 20, width: 100, height: 50 }
  it("expands a box by a share of its size on every side", () => {
    expect(expand(box, 1)).toEqual({ x: -90, y: -30, width: 300, height: 150 })
  })
  it("tells whether a view still lies inside the painted cover", () => {
    expect(encloses(expand(box, 1), box)).toBe(true)
    expect(encloses(box, expand(box, 0.1))).toBe(false)
  })
  it("joins covers without losing either box", () => {
    const joined = union(box, { x: 200, y: 0, width: 10, height: 10 })
    expect(joined).toEqual({ x: 10, y: 0, width: 200, height: 70 })
    expect(union(null, box)).toBe(box)
  })
})
