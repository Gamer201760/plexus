import { describe, expect, it } from "vitest"
import { buildBoundaryAtlas } from "@/entities/region/osm-map/boundary-geojson"
import { regionFrame } from "@/entities/region/osm-map/map-camera"
import { isChatMapCommand } from "@/shared/api/chat-map"

const atlas = buildBoundaryAtlas([
  { id: "01000000", name: "West", bounds: [85, 49, 91, 53], polygons: [] },
  { id: "02000000", name: "East", bounds: [170, 61, 191, 72], polygons: [] },
])

describe("map commands", () => {
  it("frames a group without wrapping eastern longitudes to the other side", () => {
    expect(regionFrame(atlas, ["01000000", "02000000"])).toEqual([85, 49, 191, 72])
    expect(regionFrame(atlas, ["02000000"])).toEqual([170, 61, 191, 72])
    expect(regionFrame(atlas, ["unknown"])).toBeNull()
  })
  it("rejects invalid event arguments before moving the map", () => {
    expect(isChatMapCommand({ action: "focus", region_ids: ["01000000"] })).toBe(true)
    expect(isChatMapCommand({ action: "focus", region_ids: [] })).toBe(false)
    expect(isChatMapCommand({ action: "focus", region_ids: ["invented"] })).toBe(false)
    expect(isChatMapCommand({ action: "reset", region_ids: ["01000000"] })).toBe(false)
    expect(isChatMapCommand({ action: "reset", region_ids: [] })).toBe(true)
  })
})
