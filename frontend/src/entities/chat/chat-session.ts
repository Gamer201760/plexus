import type { ChatChart, ChatTable } from "@/shared/api/chat-artifacts"
import type { ChatCalculation } from "@/shared/api/chat-calculation"
import type { ChatMapCommand } from "@/shared/api/chat-map"
import type { AnalysisJob } from "@/shared/api/road-analysis"

export interface AnalysisCommentary {
  readonly revision: string
  readonly text: string
  readonly complete: boolean
  readonly error: string | null
}

export interface ChatEntry {
  readonly analyses?: readonly AnalysisJob[]
  readonly calculations?: readonly ChatCalculation[]
  readonly commentaries?: Readonly<Record<string, AnalysisCommentary>>
  readonly id: string
  readonly role: "user" | "assistant"
  readonly content: string
  readonly complete: boolean
  readonly steps: readonly string[]
  readonly tables: readonly ChatTable[]
  readonly charts: readonly ChatChart[]
  readonly mapCommands: readonly ChatMapCommand[]
}

export interface ChatSession {
  readonly version: 1
  readonly id: string
  readonly createdAt: number
  readonly updatedAt: number
  readonly messages: ChatEntry[]
  readonly draft: string
  readonly status: string
  readonly error: string | null
}

export function createChatSession(): ChatSession {
  const now = Date.now()
  return {
    version: 1,
    id: crypto.randomUUID(),
    createdAt: now,
    updatedAt: now,
    messages: [],
    draft: "",
    status: "idle",
    error: null,
  }
}

export function chatSessionTitle(session: ChatSession): string {
  return (session.messages.find((message) => message.role === "user")?.content ?? session.draft)
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 100)
}

export const chatSessionBusy = (status: string) =>
  !["idle", "done", "stopped", "error"].includes(status)
