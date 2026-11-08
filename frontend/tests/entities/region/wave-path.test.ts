import { describe, expect, it } from "vitest"
import { wavePath } from "@/entities/region/russia-map/wave-path"

const MAINLAND = "M0,0L50,0L100,0L100,100L0,100Z"
const ISLET = "M200,200L201,200L201,201Z"

describe("wavePath", () => {
  it("drops islets smaller than the minimum size", () => {
    expect(wavePath(`${MAINLAND} ${ISLET}`, 1, 10)).toBe("M0,0L50,0L100,0L100,100L0,100Z")
  })

  it("thins points closer than the step", () => {
    expect(wavePath(MAINLAND, 60, 10)).toBe("M0,0L100,0L100,100L0,100Z")
  })

  it("keeps the largest ring when every ring is below the minimum size", () => {
    expect(wavePath(ISLET, 0.1, 50)).toBe("M200,200L201,200L201,201Z")
  })
})
