import { describe, expect, it } from "vitest"
import { buildTransitCollection } from "@/entities/region/osm-map/transit-geojson"
import type { components } from "@/shared/api"

type Link = components["schemas"]["LinkResponse"]

function link(overrides: Partial<Link> = {}): Link {
  return {
    id: "rail-1",
    region_id: "17000000",
    mode: "rail",
    season: "all",
    from: { x: null, y: null, id: "a", name: "A", lon: 40, lat: 56 },
    to: { x: null, y: null, id: "b", name: "B", lon: 41, lat: 57 },
    km: null,
    freq_per_week: null,
    freq_assumed: false,
    freq_note: null,
    vehicle: null,
    confidence: null,
    source_url: null,
    source_date: null,
    is_model: true,
    ...overrides,
  }
}

describe("buildTransitCollection", () => {
  it("draws selected-region rail and air only and clears on deselection", () => {
    const links = [
      link(),
      link({ mode: "air" }),
      link({ mode: "bus" }),
      link({ region_id: "other" }),
    ]
    expect(buildTransitCollection(links, "17000000").data.features).toHaveLength(2)
    expect(buildTransitCollection(links, null).data.features).toHaveLength(0)
    expect(buildTransitCollection(links, "next").data.features).toHaveLength(0)
  })

  it("merges opposite directions visually while preserving different modes", () => {
    const first = link()
    const reverse = link({ from: first.to, to: first.from })
    const result = buildTransitCollection([first, reverse, link({ mode: "air" })], "17000000")
    expect(result.data.features).toHaveLength(2)
    expect(result.modeled).toBe(true)
  })

  it("reports missing and invalid coordinates instead of inventing positions", () => {
    const invalid = [
      link({ from: { x: null, y: null, id: "a", name: "A" } }),
      link({ from: { x: null, y: null, id: "a", name: "A", lon: 181, lat: 56 } }),
      link({ from: { x: null, y: null, id: "a", name: "A", lon: 40, lat: Number.NaN } }),
    ]
    const result = buildTransitCollection(invalid, "17000000")
    expect(result.data.features).toHaveLength(0)
    expect(result.missing).toBe(3)
  })

  it("uses the short path across the antimeridian without mutating endpoints", () => {
    const original = link({
      from: { x: null, y: null, id: "a", name: "A", lon: 179, lat: 60 },
      to: { x: null, y: null, id: "b", name: "B", lon: -179, lat: 61 },
    })
    const result = buildTransitCollection([original], "17000000")
    expect(result.data.features[0]?.geometry.coordinates).toEqual([
      [179, 60],
      [181, 61],
    ])
    expect(original.to.lon).toBe(-179)
  })

  it("keeps all distinct selected connections without arbitrary sampling", () => {
    const links = Array.from({ length: 2000 }, (_, index) =>
      link({
        id: String(index),
        to: {
          x: null,
          y: null,
          id: String(index),
          name: String(index),
          lon: 41 + index / 10000,
          lat: 57,
        },
      }),
    )
    expect(buildTransitCollection(links, "17000000").data.features).toHaveLength(2000)
  })
})
