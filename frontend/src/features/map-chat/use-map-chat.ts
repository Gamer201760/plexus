import { useEffect, useRef, useState } from "react"
import { type ChatContext, type ChatInput, useChatStream } from "@/entities/chat"
import { isApiError } from "@/shared/api"
import type { ChatChart, ChatTable } from "@/shared/api/chat-artifacts"
import type { ChatCalculation } from "@/shared/api/chat-calculation"
import type { ChatMapCommand, MapCommandHandler } from "@/shared/api/chat-map"
import { streamStatus, updateChatRows } from "./chat-events"
import { historyContent } from "./chat-history"

export interface ChatEntry {
  readonly calculations?: readonly ChatCalculation[]
  readonly id: string
  readonly role: "user" | "assistant"
  readonly content: string
  readonly complete: boolean
  readonly steps: readonly string[]
  readonly tables: readonly ChatTable[]
  readonly charts: readonly ChatChart[]
  readonly mapCommands: readonly ChatMapCommand[]
}

export function useMapChat(context: ChatContext, onMapCommand: MapCommandHandler) {
  const mapHandler = useRef(onMapCommand)
  mapHandler.current = onMapCommand
  const [draft, setDraft] = useState("")
  const [messages, setMessages] = useState<ChatEntry[]>([])
  const [status, setStatus] = useState("idle")
  const [error, setError] = useState<string | null>(null)
  const controller = useRef<AbortController | null>(null)
  const last = useRef<ChatInput | null>(null)
  const mutation = useChatStream()
  useEffect(() => () => controller.current?.abort(), [])

  const run = async (body: ChatInput, previous: ChatEntry[]) => {
    if (controller.current) return
    const abort = new AbortController()
    controller.current = abort
    last.current = body
    const id = crypto.randomUUID()
    setMessages([
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
    ])
    setError(null)
    setStatus("connecting")
    setDraft("")
    try {
      await mutation.mutateAsync({
        body,
        signal: abort.signal,
        onEvent: (event) => {
          if (abort.signal.aborted) return
          if (event.type === "map" && event.map) mapHandler.current(event.map)
          setStatus((current) => streamStatus(current, event))
          setMessages((rows) => updateChatRows(rows, id, event))
        },
      })
    } catch (failure) {
      if (abort.signal.aborted) setStatus("stopped")
      else {
        setError(isApiError(failure) ? failure.code : "chat_connection_error")
        setStatus("error")
      }
    } finally {
      controller.current = null
    }
  }

  const send = (text = draft) => {
    const prompt = text.trim()
    if (!prompt || prompt.length > 4000) return
    const history = messages
      .filter((row) => row.complete && row.content)
      .slice(-12)
      .map((row) => ({ role: row.role, content: historyContent(row) }))
    void run({ prompt, history, context }, messages)
  }
  const retry = () => {
    if (last.current) void run(last.current, messages.slice(0, -2))
  }
  const clear = () => {
    if (controller.current) return
    setMessages([])
    setStatus("idle")
    setError(null)
    last.current = null
  }
  return {
    draft,
    setDraft,
    messages,
    status,
    error,
    send,
    retry,
    clear,
    busy: mutation.isPending,
    stop: () => controller.current?.abort(),
  }
}
