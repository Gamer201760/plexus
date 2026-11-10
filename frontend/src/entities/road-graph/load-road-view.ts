import { ApiError } from "@/shared/api/client"
import type { RoadBounds, RoadRenderView } from "@/shared/api/road-graph"
import type { RoadWorkerResult } from "./road-render.worker"

export function loadRoadView(bounds: RoadBounds, signal: AbortSignal): Promise<RoadRenderView> {
  return new Promise((resolve, reject) => {
    if (signal.aborted) {
      reject(new DOMException("Aborted", "AbortError"))
      return
    }
    const worker = new Worker(new URL("./road-render.worker.ts", import.meta.url), {
      type: "module",
    })
    const close = () => {
      signal.removeEventListener("abort", abort)
      worker.terminate()
    }
    const abort = () => {
      close()
      reject(new DOMException("Aborted", "AbortError"))
    }
    signal.addEventListener("abort", abort, { once: true })
    worker.onmessage = (event: MessageEvent<RoadWorkerResult>) => {
      close()
      if ("data" in event.data) resolve(event.data.data)
      else reject(new ApiError(event.data.error.status, event.data.error.code))
    }
    worker.onerror = () => {
      close()
      reject(new ApiError(0, "network_unavailable"))
    }
    worker.postMessage(bounds)
  })
}
