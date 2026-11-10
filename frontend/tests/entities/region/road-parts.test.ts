import type { Map as LibreMap } from "maplibre-gl"
import { afterEach, describe, expect, it, vi } from "vitest"
import { betweenRoadParts } from "@/entities/region/osm-map/road-parts"

function movingMap() {
  return { isMoving: () => true, once: vi.fn(), off: vi.fn() }
}

afterEach(() => vi.unstubAllGlobals())

describe("road uploads yield to map interaction", () => {
  it("waits for the movement to stop and then for the next frame", async () => {
    const frame = vi.fn()
    vi.stubGlobal("requestAnimationFrame", frame)
    vi.stubGlobal("cancelAnimationFrame", vi.fn())
    const map = movingMap()
    const pending = betweenRoadParts(map as unknown as LibreMap, new AbortController().signal)
    expect(frame).not.toHaveBeenCalled()
    const resume = map.once.mock.calls[0]?.[1] as () => void
    resume()
    expect(frame).toHaveBeenCalledOnce()
    const nextFrame = frame.mock.calls[0]?.[0] as () => void
    nextFrame()
    await pending
    expect(map.off).toHaveBeenCalledWith("moveend", resume)
  })

  it("releases a cancelled upload while the user is still dragging", async () => {
    const frame = vi.fn()
    vi.stubGlobal("requestAnimationFrame", frame)
    vi.stubGlobal("cancelAnimationFrame", vi.fn())
    const map = movingMap()
    const controller = new AbortController()
    const pending = betweenRoadParts(map as unknown as LibreMap, controller.signal)
    controller.abort()
    await pending
    expect(frame).not.toHaveBeenCalled()
    expect(map.off).toHaveBeenCalledWith("moveend", map.once.mock.calls[0]?.[1])
  })
})
