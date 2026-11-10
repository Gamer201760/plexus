import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import { ChatCalculationCard } from "@/features/map-chat/chat-calculation-card"
import { applyChatEvent } from "@/features/map-chat/chat-events"
import { isChatCalculation } from "@/shared/api/chat-calculation"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/chat.json"

const calculation = {
  corridor: {
    id: "corridor",
    scope: "whole_osm_ways_on_named_road_corridor_both_directions",
    road_ref: "R-1",
    origin: "A",
    destination: "B",
    way_ids: [7],
    length_km: 4,
    origin_attachment_km: 0,
    destination_attachment_km: 0,
    regions: [{ id: "1", name: "First" }],
    lines: [
      [
        [40, 44],
        [41, 45],
      ],
    ],
  },
  job_ids: ["job"],
}

describe("chat calculation", () => {
  it("frames once and displays real progress in the message", () => {
    const client = new QueryClient({ defaultOptions: { queries: { staleTime: Infinity } } })
    client.setQueryData(["road-scenario", "job"], {
      id: "job",
      region: "First",
      status: "running",
      completed: 91,
      total: 360,
    })
    const show = vi.fn()
    const content = (
      <QueryClientProvider client={client}>
        <LocaleProvider>
          <ChatCalculationCard calculation={calculation} onShow={show} />
        </LocaleProvider>
      </QueryClientProvider>
    )
    const view = render(content)
    expect(screen.getByRole("progressbar").getAttribute("value")).toBe("91")
    expect(screen.getByRole("img", { name: ru.calculation.geometry })).toBeTruthy()
    view.rerender(content)
    expect(show).toHaveBeenCalledTimes(1)
    view.unmount()
    client.clear()
  })
  it("rejects malformed geometry and retains a calculation without prose", () => {
    expect(isChatCalculation(calculation)).toBe(true)
    expect(
      isChatCalculation({
        ...calculation,
        corridor: { ...calculation.corridor, lines: [[[NaN, 1]]] },
      }),
    ).toBe(false)
    const row = {
      id: "answer",
      role: "assistant" as const,
      content: "",
      complete: false,
      steps: [],
      tables: [],
      charts: [],
      mapCommands: [],
    }
    const updated = applyChatEvent(row, { type: "calculation", text: "", code: "", calculation })
    expect(updated.calculations).toEqual([calculation])
    expect(
      applyChatEvent(updated, { type: "calculation", text: "", code: "", calculation })
        .calculations,
    ).toHaveLength(1)
  })
})
