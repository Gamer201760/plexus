import { describe, expect, it } from "vitest"
import { buildScale, roundest } from "@/features/map-explorer/scale"

const LINKS = [
  ...Array.from({ length: 19 }, () => 0),
  ...Array.from({ length: 11 }, () => 1),
  2,
  3,
  3,
  3,
  3,
  3,
  3,
  4,
  4,
  4,
  4,
  4,
  5,
  5,
  5,
  5,
  5,
  6,
  6,
  6,
  7,
  7,
  8,
  8,
  8,
  10,
  11,
  12,
  12,
  12,
  12,
  13,
  13,
  13,
  14,
  16,
  18,
  19,
  21,
  22,
  25,
  29,
  32,
  36,
  37,
  38,
  53,
  66,
  68,
  71,
  77,
  115,
]

describe("roundest", () => {
  it("picks the roundest number inside the gap", () => {
    expect(roundest(77, 115)).toBe(100)
    expect(roundest(22, 25)).toBe(25)
    expect(roundest(2, 3)).toBe(3)
    expect(roundest(0, 41_434)).toBe(40_000)
    expect(roundest(1_142_827, 1_143_224)).toBe(1_143_224)
  })
})

describe("buildScale", () => {
  it("separates the tail of a skewed metric", () => {
    const scale = buildScale(LINKS)
    expect(scale.stepOf(115)).not.toBe(scale.stepOf(38))
    expect(scale.stepOf(115)).toBe(7)
  })

  it("gives zero and missing values their own steps", () => {
    const scale = buildScale(LINKS)
    expect(scale.hasZero).toBe(true)
    expect(scale.stepOf(null)).toBe(0)
    expect(scale.stepOf(0)).toBe(1)
    expect(scale.bins[0]?.step).toBe(3)
    expect(scale.stepOf(1)).toBe(3)
  })

  it("keeps thresholds increasing and every value in its class", () => {
    const scale = buildScale(LINKS)
    const froms = scale.bins.map((bin) => bin.from)
    expect(froms).toEqual([...froms].sort((a, b) => a - b))
    expect(new Set(froms).size).toBe(froms.length)
    for (const value of LINKS.filter((item) => item > 0)) {
      const bin = scale.bins.findLast((candidate) => candidate.from <= value)
      expect(scale.stepOf(value)).toBe(bin?.step)
    }
  })

  it("uses six classes when no value is zero", () => {
    const scale = buildScale([10, 20, 40, 80, 160, 320, 640, 1280])
    expect(scale.hasZero).toBe(false)
    expect(scale.bins).toHaveLength(6)
    expect(scale.bins[0]?.step).toBe(2)
    expect(scale.bins.at(-1)?.step).toBe(7)
  })

  it("handles empty and single-valued data", () => {
    expect(buildScale([]).bins).toEqual([])
    expect(buildScale([null]).stepOf(null)).toBe(0)
    const single = buildScale([5, 5, 5])
    expect(single.bins).toEqual([{ from: 5, step: 7 }])
    expect(single.stepOf(5)).toBe(7)
  })
})
