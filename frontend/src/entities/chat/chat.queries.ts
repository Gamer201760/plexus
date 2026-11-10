import { useMutation } from "@tanstack/react-query"
import { type ChatInput, type ChatStreamEvent, streamChat } from "@/shared/api/chat-stream"

interface ChatTurn {
  readonly body: ChatInput
  readonly signal: AbortSignal
  readonly onEvent: (event: ChatStreamEvent) => void
}

export function useChatStream() {
  return useMutation({
    scope: { id: "chat-stream" },
    mutationFn: ({ body, signal, onEvent }: ChatTurn) => {
      signal.throwIfAborted()
      return streamChat(body, signal, onEvent)
    },
    retry: false,
  })
}
