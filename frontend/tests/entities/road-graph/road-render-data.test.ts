import { describe, expect, it } from "vitest"
import { prepareRoadView } from "@/entities/road-graph/road-render-data"
import type { RoadSegment } from "@/shared/api/road-graph"

function segment(id: number): RoadSegment {
  return {
    way_id: id,
    name: `Road ${id}`,
    highway: "primary",
    speed_kmh: 60,
    source_node: id,
    target_node: id + 1,
    coordinates: [
      [38, 54],
      [39, 55],
    ],
  }
}

describe("road geometry prepared outside the UI thread", () => {
  it("keeps every disconnected segment and its click metadata in the blob", async () => {
    const segments = [
      segment(1),
      segment(1),
      ...Array.from({ length: 20 }, (_, i) => segment(i + 2)),
    ]
    const view = prepareRoadView({
      segments,
      matched: 50,
      truncated: false,
      version: "test",
      detail: "full",
    })
    const geometry = JSON.parse((await view.geometry[0]?.text()) ?? '{"features":[]}')
    expect(view.segments).toHaveLength(12)
    expect(view.segmentCount).toBe(segments.length)
    expect(geometry.features).toHaveLength(segments.length)
    expect(new Set(geometry.features.map((f: { id: number }) => f.id)).size).toBe(segments.length)
    for (const [i, road] of segments.entries()) {
      expect(geometry.features[i].geometry.coordinates).toEqual(road.coordinates)
      expect(geometry.features[i].properties).toMatchObject({
        way_id: road.way_id,
        source_node: road.source_node,
        name: road.name,
      })
    }
  })

  it("bounds each upload while preserving roads across chunk boundaries", async () => {
    const segments = Array.from({ length: 4005 }, (_, index) => segment(index))
    const view = prepareRoadView({
      segments,
      matched: 4005,
      truncated: false,
      version: "test",
      detail: "full",
    })
    const parts = await Promise.all(
      view.geometry.map(async (blob) => JSON.parse(await blob.text())),
    )
    expect(parts.map((part) => part.features.length)).toEqual([2000, 2000, 5])
    const features = parts.flatMap((part) => part.features)
    expect(features.map((feature) => feature.properties.way_id)).toEqual(
      segments.map((road) => road.way_id),
    )
    expect(new Set(features.map((feature) => feature.id)).size).toBe(4005)
  })

  it("does not invent roads for an empty response", async () => {
    const view = prepareRoadView({
      segments: [],
      matched: 0,
      truncated: false,
      version: "test",
      detail: "full",
    })
    expect(view.segmentCount).toBe(0)
    expect(JSON.parse((await view.geometry[0]?.text()) ?? '{"features":[]}').features).toEqual([])
  })
})
