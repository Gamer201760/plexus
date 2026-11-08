import { readFileSync } from "node:fs"
import { describe, expect, it } from "vitest"
import { contains, intersects, mainlandBox } from "@/entities/region/russia-map/map-shapes"

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
