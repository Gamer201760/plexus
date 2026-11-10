import { useMutation } from "@tanstack/react-query"
import { type ChatInput, type ChatStreamEvent, streamChat } from "@/shared/api/chat-stream"

interface ChatTurn {
  readonly body: ChatInput
  readonly signal: AbortSignal
  readonly onEvent: (event: ChatStreamEvent) => void
}

export function useChatStream() {
  return useMutation({
    mutationFn: ({ body, signal, onEvent }: ChatTurn) => streamChat(body, signal, onEvent),
    retry: false,
  })
}
