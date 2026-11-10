import { useEffect, useRef } from "react"
import {
  type AnalysisCommentary,
  type ChatContext,
  type ChatEntry,
  type ChatInput,
  chatSessionBusy,
  useChatSessions,
  useChatStream,
} from "@/entities/chat"
import { isApiError } from "@/shared/api"
import type { MapCommandHandler } from "@/shared/api/chat-map"
import { streamStatus, updateChatRows } from "./chat-events"
import { historyContent } from "./chat-history"

export type { ChatEntry } from "@/entities/chat"

function historyOf(messages: ChatEntry[]) {
  return messages
    .filter((row) => row.complete && (row.content || row.analyses?.length))
    .slice(-12)
    .map((row) => ({ role: row.role, content: historyContent(row) }))
}

export function useMapChat(context: ChatContext, onMapCommand: MapCommandHandler) {
  const archive = useChatSessions()
  const session = archive.active
  const { update } = archive
  const mapHandler = useRef(onMapCommand)
  mapHandler.current = onMapCommand
  const activeId = useRef(session.id)
  activeId.current = session.id
  const controllers = useRef(new Map<string, AbortController>())
  const requests = useRef(new Map<string, ChatInput>())
  const mutation = useChatStream()
  useEffect(() => {
    const running = controllers.current
    return () => {
      for (const controller of running.values()) controller.abort()
    }
  }, [])

  const run = async (body: ChatInput, previous: ChatEntry[]) => {
    const sessionId = session.id
    if (controllers.current.has(sessionId)) return
    const abort = new AbortController()
    controllers.current.set(sessionId, abort)
    requests.current.set(sessionId, body)
    const id = crypto.randomUUID()
    update(sessionId, (current) => ({
      ...current,
      draft: "",
      error: null,
      status: "connecting",
      messages: [
        ...previous,
        {
          id: crypto.randomUUID(),
          role: "user",
          content: body.prompt,
          complete: true,
          steps: [],
          tables: [],
          charts: [],
          mapCommands: [],
        },
        {
          id,
          role: "assistant",
          content: "",
          complete: false,
          steps: [],
          tables: [],
          charts: [],
          mapCommands: [],
        },
      ],
    }))
    try {
      await mutation.mutateAsync({
        body,
        signal: abort.signal,
        onEvent: (event) => {
          if (abort.signal.aborted) return
          if (event.type === "map" && event.map && activeId.current === sessionId)
            mapHandler.current(event.map)
          update(sessionId, (current) => ({
            ...current,
            status: streamStatus(current.status, event),
            messages: updateChatRows(current.messages, id, event),
          }))
        },
      })
    } catch (failure) {
      update(sessionId, (current) => ({
        ...current,
        status: abort.signal.aborted ? "stopped" : "error",
        error: abort.signal.aborted
          ? null
          : isApiError(failure)
            ? failure.code
            : "chat_connection_error",
      }))
    } finally {
      controllers.current.delete(sessionId)
    }
  }
  const send = (text = session.draft) => {
    const prompt = text.trim()
    if (!prompt || prompt.length > 4000) return
    void run({ prompt, history: historyOf(session.messages), context }, session.messages)
  }
  const retry = () => {
    const prompt = session.messages.at(-2)?.content
    if (!prompt) return
    const previous = session.messages.slice(0, -2)
    const body = requests.current.get(session.id) ?? {
      prompt,
      history: historyOf(previous),
      context,
    }
    void run(body, previous)
  }
  const saveCommentary = (messageId: string, analysisId: string, value: AnalysisCommentary) => {
    update(session.id, (current) => ({
      ...current,
      messages: current.messages.map((row) =>
        row.id === messageId
          ? { ...row, commentaries: { ...row.commentaries, [analysisId]: value } }
          : row,
      ),
    }))
  }
  return {
    draft: session.draft,
    setDraft: (draft: string) => update(session.id, (current) => ({ ...current, draft })),
    messages: session.messages,
    status: session.status,
    error: session.error,
    sessionId: session.id,
    sessions: archive.sessions,
    selectSession: archive.select,
    newSession: archive.create,
    deleteSession: (id: string) => {
      controllers.current.get(id)?.abort()
      requests.current.delete(id)
      archive.remove(id)
    },
    storageIssue: archive.storageIssue,
    retrySave: archive.save,
    saveCommentary,
    send,
    retry,
    busy: chatSessionBusy(session.status),
    stop: () => controllers.current.get(session.id)?.abort(),
  }
}
