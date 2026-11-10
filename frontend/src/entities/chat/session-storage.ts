import { type ChatSession, chatSessionBusy, createChatSession } from "./chat-session"
import { isChatSession } from "./session-validation"

const PREFIX = "plexus.chat.session.v1."
const ACTIVE = "plexus.chat.active.v1"

export interface ChatArchive {
  readonly sessions: ChatSession[]
  readonly activeId: string
}

export function readChatArchive(): ChatArchive & { readonly issue: boolean } {
  const sessions: ChatSession[] = []
  let activeId: string | null = null
  let issue = false
  try {
    activeId = localStorage.getItem(ACTIVE)
    for (let index = 0; index < localStorage.length; index++) {
      const key = localStorage.key(index)
      if (!key?.startsWith(PREFIX)) continue
      try {
        const value: unknown = JSON.parse(localStorage.getItem(key) ?? "null")
        if (!isChatSession(value) || key !== PREFIX + value.id) {
          issue = true
          continue
        }
        sessions.push({
          ...value,
          status: chatSessionBusy(value.status) ? "stopped" : value.status,
        })
      } catch {
        issue = true
      }
    }
  } catch {
    issue = true
  }
  if (!sessions.length) sessions.push(createChatSession())
  sessions.sort((a, b) => b.updatedAt - a.updatedAt)
  const selected = sessions.find((session) => session.id === activeId) ?? sessions[0]
  return { sessions, activeId: selected?.id ?? "", issue }
}

export function writeChatArchive(
  archive: ChatArchive,
  saved: Map<string, ChatSession>,
  deleted: ReadonlySet<string> = new Set(),
): void {
  for (const id of deleted) {
    localStorage.removeItem(PREFIX + id)
    saved.delete(id)
  }
  for (const session of archive.sessions) {
    if (deleted.has(session.id) || saved.get(session.id) === session) continue
    localStorage.setItem(PREFIX + session.id, JSON.stringify(session))
    saved.set(session.id, session)
  }
  localStorage.setItem(ACTIVE, archive.activeId)
}
