import { useCallback, useEffect, useRef, useState } from "react"
import { type ChatSession, createChatSession } from "./chat-session"
import { type ChatArchive, readChatArchive, writeChatArchive } from "./session-storage"

export function useChatSessions() {
  const [archive, setArchive] = useState(readChatArchive)
  const [storageIssue, setStorageIssue] = useState<"read" | "write" | null>(
    archive.issue ? "read" : null,
  )
  const current = useRef<ChatArchive>(archive)
  current.current = archive
  const deleted = useRef(new Set<string>())
  const saved = useRef(new Map<string, ChatSession>())
  const save = useCallback(() => {
    try {
      writeChatArchive(current.current, saved.current, deleted.current)
      setStorageIssue((issue) => (issue === "write" ? null : issue))
    } catch {
      setStorageIssue("write")
    }
  }, [])
  useEffect(() => {
    const flush = () => {
      current.current = archive
      save()
    }
    if (typeof window.requestIdleCallback === "function") {
      const handle = window.requestIdleCallback(flush)
      return () => window.cancelIdleCallback(handle)
    }
    const timer = window.setTimeout(flush)
    return () => window.clearTimeout(timer)
  }, [archive, save])
  useEffect(() => {
    window.addEventListener("pagehide", save)
    return () => {
      window.removeEventListener("pagehide", save)
      save()
    }
  }, [save])
  const update = useCallback((id: string, change: (session: ChatSession) => ChatSession) => {
    setArchive((previous) => ({
      ...previous,
      sessions: previous.sessions.map((session) =>
        session.id === id ? { ...change(session), updatedAt: Date.now() } : session,
      ),
    }))
  }, [])
  const select = (id: string) => {
    if (archive.sessions.some((session) => session.id === id))
      setArchive((previous) => ({ ...previous, activeId: id }))
  }
  const create = () => {
    const empty = archive.sessions.find((session) => !session.messages.length && !session.draft)
    if (empty) {
      select(empty.id)
      return
    }
    const session = createChatSession()
    setArchive((previous) => ({
      ...previous,
      activeId: session.id,
      sessions: [session, ...previous.sessions],
    }))
  }
  const remove = (id: string) => {
    deleted.current.add(id)
    setArchive((previous) => {
      const remaining = previous.sessions.filter((session) => session.id !== id)
      const sessions = remaining.length ? remaining : [createChatSession()]
      const next = [...sessions].sort((a, b) => b.updatedAt - a.updatedAt)[0]
      return {
        ...previous,
        sessions,
        activeId: previous.activeId === id ? (next?.id ?? "") : previous.activeId,
      }
    })
  }
  const active =
    archive.sessions.find((session) => session.id === archive.activeId) ?? archive.sessions[0]
  if (!active) throw new Error("Chat archive has no active session")
  return {
    active,
    sessions: [...archive.sessions].sort((a, b) => b.updatedAt - a.updatedAt),
    update,
    select,
    create,
    remove,
    storageIssue,
    save,
  }
}
