import { isChatAnalysis } from "./chat-analysis"
import { isChatChart, isChatTable } from "./chat-artifacts"
import { isChatCalculation } from "./chat-calculation"
import { isChatMapCommand } from "./chat-map"
import { ApiError, api, codeOf } from "./client"
import type { components } from "./schema.gen"

export type ChatInput = components["schemas"]["ChatInput"]
export type ChatContext = components["schemas"]["ChatContextInput"]
export type ChatStreamEvent = components["schemas"]["ChatStreamEvent"]

const ARTIFACTS: Record<string, (value: unknown) => boolean> = {
  table: isChatTable,
  chart: isChatChart,
  map: isChatMapCommand,
  calculation: isChatCalculation,
  analysis: isChatAnalysis,
}

function parseEvent(line: string): ChatStreamEvent {
  const value: unknown = JSON.parse(line)
  if (
    typeof value !== "object" ||
    value === null ||
    !("type" in value) ||
    ![
      "status",
      "delta",
      "done",
      "error",
      "table",
      "chart",
      "map",
      "calculation",
      "analysis",
    ].includes(String(value.type)) ||
    !("text" in value) ||
    typeof value.text !== "string" ||
    !("code" in value) ||
    typeof value.code !== "string"
  )
    throw new ApiError(502, "chat_stream_error")
  const artifact = value as Record<string, unknown>
  const validate = ARTIFACTS[String(value.type)]
  if (validate && !validate(artifact[String(value.type)]))
    throw new ApiError(502, "chat_stream_error")
  return value as ChatStreamEvent
}

export async function streamChat(
  body: ChatInput,
  signal: AbortSignal,
  onEvent: (event: ChatStreamEvent) => void,
): Promise<void> {
  const { data, response, error } = await api.POST("/api/v1/chat", {
    body,
    signal,
    parseAs: "stream",
  })
  if (!response.ok) throw new ApiError(response.status, codeOf(error))
  if (!data) throw new ApiError(502, "chat_stream_error")
  const reader = data.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  let complete = false
  const consume = (line: string) => {
    if (!line.trim()) return
    const event = parseEvent(line)
    if (event.type === "error") throw new ApiError(502, event.code)
    if (event.type === "done") complete = true
    onEvent(event)
  }
  try {
    while (true) {
      const { value, done } = await reader.read()
      buffer += decoder.decode(value, { stream: !done })
      const lines = buffer.split("\n")
      buffer = lines.pop() ?? ""
      for (const line of lines) consume(line)
      if (buffer.length > 2000000) throw new ApiError(502, "chat_stream_error")
      if (done) break
    }
    consume(buffer)
    if (!complete) throw new ApiError(502, "chat_stream_error")
  } finally {
    await reader.cancel().catch(() => undefined)
    reader.releaseLock()
  }
}
