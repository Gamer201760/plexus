import type { ReactNode } from "react"

const SUBSCRIPT = /([A-Za-zα-ωΑ-Ω])_([a-z]+)/g

export function formulaParts(formula: string): ReactNode[] {
  const parts: ReactNode[] = []
  let last = 0
  for (const match of formula.matchAll(SUBSCRIPT)) {
    const index = match.index ?? 0
    parts.push(formula.slice(last, index), match[1])
    parts.push(<sub key={index}>{match[2]}</sub>)
    last = index + match[0].length
  }
  parts.push(formula.slice(last))
  return parts
}
