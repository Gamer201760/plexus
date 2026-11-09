import { useCallback, useEffect, useRef } from "react"
import { motionMs } from "../../../motion"

export function isPrintableKey(key: string, modified: boolean): boolean {
  return key.length === 1 && key !== " " && !modified
}

export function findMatch(labels: readonly string[], query: string, from: number): number | null {
  const needle = query.toLocaleLowerCase()
  const repeated = [...needle].every((char) => char === needle[0])
  const search = repeated ? (needle[0] ?? "") : needle
  const start = repeated ? from + 1 : Math.max(from, 0)
  for (let step = 0; step < labels.length; step += 1) {
    const index = (start + step) % labels.length
    if (labels[index]?.toLocaleLowerCase().startsWith(search)) return index
  }
  return null
}

export interface Typeahead {
  readonly busy: () => boolean
  readonly type: (char: string, from: number) => number | null
}

export function useTypeahead(labels: readonly string[]): Typeahead {
  const buffer = useRef("")
  const timer = useRef<number | undefined>(undefined)

  useEffect(() => () => window.clearTimeout(timer.current), [])

  const busy = useCallback(() => buffer.current !== "", [])

  const type = useCallback(
    (char: string, from: number) => {
      window.clearTimeout(timer.current)
      buffer.current += char
      timer.current = window.setTimeout(() => {
        buffer.current = ""
      }, motionMs("--delay-typeahead"))
      return findMatch(labels, buffer.current, from)
    },
    [labels],
  )

  return { busy, type }
}
