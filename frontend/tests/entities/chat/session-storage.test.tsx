import { beforeEach, describe, expect, it } from "vitest"
import { createChatSession } from "@/entities/chat/chat-session"
import { readChatArchive, writeChatArchive } from "@/entities/chat/session-storage"

beforeEach(() => localStorage.clear())

describe("chat archive storage", () => {
  it("reads valid sessions even when another record is corrupted", () => {
    const session = { ...createChatSession(), draft: "Saved question", status: "writing" }
    writeChatArchive({ sessions: [session], activeId: session.id }, new Map())
    localStorage.setItem("plexus.chat.session.v1.broken", "{")
    const restored = readChatArchive()
    expect(restored.issue).toBe(true)
    expect(restored.sessions).toHaveLength(1)
    expect(restored.sessions[0]?.draft).toBe("Saved question")
    expect(restored.sessions[0]?.status).toBe("stopped")
    expect(localStorage.getItem("plexus.chat.session.v1.broken")).toBe("{")
  })

  it("writes individual sessions without removing sessions from another tab", () => {
    const first = createChatSession()
    const second = createChatSession()
    writeChatArchive({ sessions: [first], activeId: first.id }, new Map())
    writeChatArchive({ sessions: [second], activeId: second.id }, new Map())
    expect(readChatArchive().sessions).toHaveLength(2)
    expect(readChatArchive().activeId).toBe(second.id)
  })
})
