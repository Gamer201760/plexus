import { useEffect, useRef, useState } from "react"
import { isApiError } from "@/shared/api"
import { useChatStream } from "./chat.queries"
import type { AnalysisCommentary } from "./chat-session"

export function useAnalysisCommentary(
  analysisId: string,
  revision: string | null,
  saved?: AnalysisCommentary | undefined,
  onChange?: ((value: AnalysisCommentary) => void) | undefined,
) {
  const [text, setText] = useState(saved?.text ?? "")
  const [error, setError] = useState<string | null>(saved?.error ?? null)
  const [complete, setComplete] = useState(saved?.complete ?? false)
  const [attempt, setAttempt] = useState(0)
  const savedRef = useRef(saved)
  savedRef.current = saved
  const changeRef = useRef(onChange)
  changeRef.current = onChange
  const { mutateAsync, isPending } = useChatStream()
  useEffect(() => {
    if (revision === null) return
    const existing = savedRef.current
    if (attempt === 0 && existing?.revision === revision) {
      setText(existing.text)
      setComplete(existing.complete)
      setError(existing.complete ? null : (existing.error ?? "chat_stream_error"))
      return
    }
    const abort = new AbortController()
    let value: AnalysisCommentary = { revision, text: "", complete: false, error: null }
    const publish = (next: AnalysisCommentary) => {
      value = next
      setText(value.text)
      setComplete(value.complete)
      setError(value.error)
      changeRef.current?.(value)
    }
    publish(value)
    void mutateAsync({
      body: { prompt: "Review the completed analysis", analysis_id: analysisId },
      signal: abort.signal,
      onEvent: (event) => {
        if (abort.signal.aborted) return
        if (event.type === "delta") publish({ ...value, text: value.text + (event.text ?? "") })
        if (event.type === "done") publish({ ...value, complete: true })
      },
    }).catch((failure: unknown) => {
      if (!abort.signal.aborted)
        publish({ ...value, error: isApiError(failure) ? failure.code : "chat_connection_error" })
    })
    return () => {
      abort.abort()
      if (!value.complete && !value.error)
        changeRef.current?.({ ...value, error: "chat_stream_error" })
    }
  }, [analysisId, revision, attempt, mutateAsync])
  return {
    text,
    error,
    complete,
    pending: isPending,
    retry: () => setAttempt((value) => value + 1),
  }
}
