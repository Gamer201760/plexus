import { describe, expect, it } from "vitest"
import { coversRoadViewport, roadViewport } from "@/entities/road-graph/road-viewport"

describe("road viewport cache", () => {
  it("reuses the buffered area for a small pan but refreshes outside it", () => {
    const coverage = roadViewport([38, 54, 43, 57, 7])
    expect(coversRoadViewport(coverage, [38.1, 54, 43.1, 57, 7])).toBe(true)
    expect(coversRoadViewport(coverage, [42, 54, 47, 57, 7])).toBe(false)
    expect(coversRoadViewport(coverage, [38, 54, 43, 57, 9])).toBe(false)
  })

  it("keeps padded requests within API coordinate limits", () => {
    expect(roadViewport([-179, -84, 179, 84, 4])).toEqual([-180, -85, 180, 85, 4])
  })

  it("covers the complete viewport after rounding", () => {
    const input = [-1.123456, 53.987654, 42.123456, 56.987654, 7.1] as const
    const result = roadViewport(input)
    expect(result[0]).toBeLessThanOrEqual(input[0])
    expect(result[1]).toBeLessThanOrEqual(input[1])
    expect(result[2]).toBeGreaterThanOrEqual(input[2])
    expect(result[3]).toBeGreaterThanOrEqual(input[3])
  })

  it("reuses geometry within a road detail level", () => {
    expect(roadViewport([38, 54, 43, 57, 7.1])).toEqual(roadViewport([38, 54, 43, 57, 8.9]))
    expect(roadViewport([38, 54, 43, 57, 9])).not.toEqual(roadViewport([38, 54, 43, 57, 8.9]))
  })
})
