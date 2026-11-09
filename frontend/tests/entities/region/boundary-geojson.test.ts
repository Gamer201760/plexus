import { describe, expect, it } from "vitest"
import { buildBoundaryAtlas } from "@/entities/region/osm-map/boundary-geojson"
import type { RegionBoundary } from "@/entities/region"

const ring: [number, number][] = [
  [60, 50],
  [70, 50],
  [70, 60],
  [60, 50],
]

function region(id: string, bounds: [number, number, number, number]): RegionBoundary {
  return { id, name: `R${id}`, bounds, polygons: [[ring]] }
}

describe("buildBoundaryAtlas", () => {
  it("maps numeric feature ids back to region ids", () => {
    const atlas = buildBoundaryAtlas([region("01000000", [60, 50, 70, 60])])
    const feature = atlas.featureOf.get("01000000")
    expect(feature?.id).toBe(1000000)
    expect(atlas.regionOf.get(1000000)).toBe("01000000")
    expect(atlas.collection.features[0]?.geometry.type).toBe("MultiPolygon")
  })

  it("unions region bounds into the home view", () => {
    const atlas = buildBoundaryAtlas([
      region("01000000", [60, 50, 70, 60]),
      region("02000000", [20, 44, 30, 55]),
      region("03000000", [170, 60, 190, 72]),
    ])
    expect(atlas.home).toEqual([20, 44, 190, 72])
  })

  it("skips duplicates and non-numeric ids", () => {
    const atlas = buildBoundaryAtlas([
      region("01000000", [60, 50, 70, 60]),
      region("01000000", [0, 0, 1, 1]),
      region("ext", [0, 0, 1, 1]),
    ])
    expect(atlas.collection.features).toHaveLength(1)
    expect(atlas.home).toEqual([60, 50, 70, 60])
  })
})
