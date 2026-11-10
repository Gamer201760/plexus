import { afterEach, describe, expect, it, vi } from "vitest"
import { loadRoadView } from "@/entities/road-graph/load-road-view"

const instances: TestWorker[] = []
class TestWorker {
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: (() => void) | null = null
  terminate = vi.fn()
  postMessage = vi.fn()
  constructor() {
    instances.push(this)
  }
}

afterEach(() => {
  instances.length = 0
  vi.unstubAllGlobals()
})

describe("road loading cancellation", () => {
  it("terminates obsolete workers when the viewport request is cancelled", async () => {
    vi.stubGlobal("Worker", TestWorker)
    const controller = new AbortController()
    const pending = loadRoadView([38, 54, 43, 57, 8], controller.signal)
    const rejection = expect(pending).rejects.toMatchObject({ name: "AbortError" })
    controller.abort()
    await rejection
    expect(instances[0]?.terminate).toHaveBeenCalledOnce()
  })

  it("does not start a worker for an already cancelled request", async () => {
    vi.stubGlobal("Worker", TestWorker)
    const controller = new AbortController()
    controller.abort()
    await expect(loadRoadView([38, 54, 43, 57, 8], controller.signal)).rejects.toMatchObject({
      name: "AbortError",
    })
    expect(instances).toHaveLength(0)
  })

  it("preserves API failure details and releases its worker", async () => {
    vi.stubGlobal("Worker", TestWorker)
    const pending = loadRoadView([38, 54, 43, 57, 8], new AbortController().signal)
    const rejection = expect(pending).rejects.toMatchObject({ status: 503, code: "unavailable" })
    instances[0]?.onmessage?.({
      data: { error: { status: 503, code: "unavailable" } },
    } as MessageEvent)
    await rejection
    expect(instances[0]?.terminate).toHaveBeenCalledOnce()
  })
})
