import { describe, expect, it } from "vitest"
import { presentMessage } from "@/features/map-chat/message-presentation"

describe("message presentation", () => {
  it("folds source paragraphs while retaining caveats", () => {
    const value = presentMessage(
      "Answer\r\n\r\nSources: /api/v1/regions\r\n\r\nSources: uncertain coverage",
    )
    expect(value.text).toBe("Answer\n\nSources: uncertain coverage")
    expect(value.details).toBe("Sources: /api/v1/regions")
  })
  it("retains explanation after scope and normalizes list markers", () => {
    const value = presentMessage(
      "Scope: summer. Comparison changes with season.\n\n\u2022 First\n\u2022 Second",
    )
    expect(value.text).toBe("Comparison changes with season.\n\n- First\n- Second")
    expect(value.details).toBe("Scope: summer.")
  })
  it("preserves fenced content and markdown tables", () => {
    const code = "```text\nSources: keep this\n```"
    const table = "| Region | Value |\n| --- | ---: |\n| One | 2 |"
    expect(presentMessage(`${code}\n\n${table}`).text).toBe(`${code}\n\n${table}`)
  })
})
