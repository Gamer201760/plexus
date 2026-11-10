import { createElement } from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it } from "vitest"
import { ChatMessage } from "@/shared/ui/data-display/chat-message/chat-message"
import { normalizeMath } from "@/shared/ui/data-display/chat-message/normalize-math"

const formula = String.raw`H_i=\sum_j M_j f(c_{ij})`

describe("chat mathematics", () => {
  it("normalizes legacy parentheses and variable notation", () => {
    expect(normalizeMath(`(${formula}), (M_j), (c_{ij}), (f)`)).toBe(
      `$${formula}$, $M_j$, $c_{ij}$, $f$`,
    )
  })
  it("handles standard delimiters without changing code or prose", () => {
    expect(normalizeMath(String.raw`\(M_j\)`)).toBe("$M_j$")
    expect(normalizeMath(String.raw`\[H_i\]`)).toBe("\n\n$$\nH_i\n$$\n\n")
    const protectedText = "(summer only) `M_j`\n\n```latex\n(M_j)\n```\n\n$M_j$"
    expect(normalizeMath(protectedText)).toBe(protectedText)
    expect(normalizeMath("[link](https://example.org/a_(b))")).toBe(
      "[link](https://example.org/a_(b))",
    )
  })
  it("renders the equation as accessible MathML", () => {
    const html = renderToStaticMarkup(
      createElement(ChatMessage, { speaker: "assistant", text: `(${formula})`, label: "Answer" }),
    )
    expect(html).toContain("<math")
    expect(html).toContain("<msub>")
    expect(html).not.toContain("katex-error")
  })
})
