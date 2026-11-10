import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { act, renderHook, waitFor } from "@testing-library/react"
import type { ReactNode } from "react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { useMapChat } from "@/features/map-chat/use-map-chat"
import { type ChatStreamEvent, streamChat } from "@/shared/api/chat-stream"

vi.mock("@/shared/api/chat-stream", async (load) => ({
  ...(await load<typeof import("@/shared/api/chat-stream")>()),
  streamChat: vi.fn(),
}))

const clients: QueryClient[] = []
function setup() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  clients.push(client)
  const onMap = vi.fn()
  const wrapper = ({ children }: { readonly children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  )
  return {
    ...renderHook(
      () =>
        useMapChat(
          { region_id: null, season: "summer", network_mode: "road", metric: "hansen" },
          onMap,
        ),
      { wrapper },
    ),
    onMap,
  }
}

beforeEach(() => {
  localStorage.clear()
})
afterEach(() => {
  vi.restoreAllMocks()
  vi.mocked(streamChat).mockReset()
  clients.splice(0).forEach((client) => {
    client.clear()
  })
})

describe("saved chat sessions", () => {
  it("keeps streamed answers in their own chats and restores chats and drafts after remount", async () => {
    const pending: { emit: (event: ChatStreamEvent) => void; finish: () => void }[] = []
    vi.mocked(streamChat).mockImplementation(
      (_body, _signal, emit) =>
        new Promise<void>((finish) => {
          pending.push({ emit, finish })
        }),
    )
    const first = setup()
    const firstId = first.result.current.sessionId
    act(() => first.result.current.send("First question"))
    await waitFor(() => expect(pending).toHaveLength(1))
    act(() => first.result.current.newSession())
    const secondId = first.result.current.sessionId
    expect(secondId).not.toBe(firstId)
    act(() => first.result.current.send("Second question"))
    await act(async () => {
      pending[0]?.emit({ type: "delta", text: "First answer", code: "" })
      pending[0]?.emit({
        type: "map",
        text: "",
        code: "",
        map: { action: "reset", region_ids: [] },
      })
      pending[0]?.emit({ type: "done", text: "", code: "" })
      pending[0]?.finish()
    })
    await waitFor(() => expect(pending).toHaveLength(2))
    expect(first.result.current.messages[1]?.content).toBe("")
    expect(first.onMap).not.toHaveBeenCalled()
    await act(async () => {
      pending[1]?.emit({ type: "delta", text: "Second answer", code: "" })
      pending[1]?.emit({ type: "done", text: "", code: "" })
      pending[1]?.finish()
    })
    act(() => first.result.current.selectSession(firstId))
    expect(first.result.current.messages[1]?.content).toBe("First answer")
    act(() => first.result.current.setDraft("Unsent follow-up"))
    first.unmount()
    const restored = setup()
    expect(restored.result.current.sessionId).toBe(firstId)
    expect(restored.result.current.sessions).toHaveLength(2)
    expect(restored.result.current.draft).toBe("Unsent follow-up")
    act(() => restored.result.current.selectSession(secondId))
    expect(restored.result.current.messages[1]?.content).toBe("Second answer")
    expect(restored.result.current.draft).toBe("")
    expect(streamChat).toHaveBeenCalledTimes(2)
    restored.unmount()
  })

  it("reuses an empty chat instead of adding blank duplicates", () => {
    const chat = setup()
    const id = chat.result.current.sessionId
    act(() => chat.result.current.newSession())
    expect(chat.result.current.sessionId).toBe(id)
    expect(chat.result.current.sessions).toHaveLength(1)
    chat.unmount()
  })

  it("deletes saved chats permanently and replaces the last chat", () => {
    const chat = setup()
    const firstId = chat.result.current.sessionId
    act(() => chat.result.current.setDraft("First draft"))
    act(() => chat.result.current.newSession())
    const secondId = chat.result.current.sessionId
    act(() => chat.result.current.setDraft("Second draft"))
    act(() => chat.result.current.retrySave())
    act(() => chat.result.current.deleteSession(firstId))
    expect(chat.result.current.sessionId).toBe(secondId)
    act(() => chat.result.current.retrySave())
    expect(localStorage.getItem(`plexus.chat.session.v1.${firstId}`)).toBeNull()
    act(() => chat.result.current.deleteSession(secondId))
    expect(chat.result.current.sessions).toHaveLength(1)
    expect(chat.result.current.sessionId).not.toBe(secondId)
    expect(chat.result.current.draft).toBe("")
    chat.unmount()
    const restored = setup()
    expect(restored.result.current.sessions).toHaveLength(1)
    expect(restored.result.current.draft).toBe("")
    restored.unmount()
  })

  it("aborts a deleted chat stream and ignores later events", async () => {
    let signal: AbortSignal | undefined
    let emit: ((event: ChatStreamEvent) => void) | undefined
    let finish: (() => void) | undefined
    vi.mocked(streamChat).mockImplementation((_body, abort, handler) => {
      signal = abort
      emit = handler
      return new Promise<void>((resolve) => {
        finish = resolve
      })
    })
    const chat = setup()
    const deletedId = chat.result.current.sessionId
    act(() => chat.result.current.send("Delete during response"))
    await waitFor(() => expect(signal).toBeDefined())
    act(() => chat.result.current.deleteSession(deletedId))
    expect(signal?.aborted).toBe(true)
    await act(async () => {
      emit?.({ type: "delta", text: "Late answer", code: "" })
      finish?.()
    })
    expect(chat.result.current.messages).toHaveLength(0)
    expect(chat.result.current.sessions.some((session) => session.id === deletedId)).toBe(false)
    chat.unmount()
  })

  it("retains the draft and reports a storage failure with a working save retry", () => {
    const chat = setup()
    act(() => chat.result.current.setDraft("Keep this draft"))
    const write = vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new DOMException("Full", "QuotaExceededError")
    })
    act(() => chat.result.current.retrySave())
    expect(chat.result.current.storageIssue).toBe("write")
    expect(chat.result.current.draft).toBe("Keep this draft")
    write.mockRestore()
    act(() => chat.result.current.retrySave())
    expect(chat.result.current.storageIssue).toBeNull()
    chat.unmount()
    const restored = setup()
    expect(restored.result.current.draft).toBe("Keep this draft")
    restored.unmount()
  })
})
