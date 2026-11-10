import { afterEach, describe, expect, it, vi } from "vitest"
import { type ChatStreamEvent, streamChat } from "@/shared/api/chat-stream"
import chatCopy from "@/shared/i18n/locales/ru/chat.json"

const post = vi.hoisted(() => vi.fn())
vi.mock("@/shared/api/client", async (importOriginal) => {
  const original = await importOriginal<typeof import("@/shared/api/client")>()
  return { ...original, api: { POST: post } }
})

function responseStream(text: string) {
  const bytes = new TextEncoder().encode(text)
  return new ReadableStream<Uint8Array>({
    start(controller) {
      for (let i = 0; i < bytes.length; i += 3) controller.enqueue(bytes.slice(i, i + 3))
      controller.close()
    },
  })
}

function mockResponse(text: string) {
  post.mockResolvedValue({
    data: responseStream(text),
    response: new Response(null, { status: 200 }),
  })
}

afterEach(() => vi.restoreAllMocks())

describe("chat stream", () => {
  it("decodes split Cyrillic bytes and multiple events", async () => {
    mockResponse(
      [
        { type: "delta", text: chatCopy.title, code: "" },
        { type: "delta", text: chatCopy.example, code: "" },
        { type: "done", text: "", code: "" },
      ]
        .map((event) => JSON.stringify(event))
        .join("\n"),
    )
    const events: ChatStreamEvent[] = []
    await streamChat({ prompt: "Hello" }, new AbortController().signal, (event) =>
      events.push(event),
    )
    expect(
      events
        .filter((event) => event.type === "delta")
        .map((event) => event.text)
        .join(""),
    ).toBe(chatCopy.title + chatCopy.example)
    expect(events.at(-1)?.type).toBe("done")
  })

  it("rejects premature EOF instead of showing a completed answer", async () => {
    mockResponse(JSON.stringify({ type: "delta", text: "Partial", code: "" }))
    await expect(
      streamChat({ prompt: "Hello" }, new AbortController().signal, () => undefined),
    ).rejects.toMatchObject({ code: "chat_stream_error" })
  })

  it("preserves safe server error codes", async () => {
    mockResponse(JSON.stringify({ type: "error", text: "", code: "chat_auth_required" }))
    await expect(
      streamChat({ prompt: "Hello" }, new AbortController().signal, () => undefined),
    ).rejects.toMatchObject({ code: "chat_auth_required" })
  })
})
