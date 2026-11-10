import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"
import type { AnalysisCommentary } from "@/entities/chat"
import { ChatAnalysisCard } from "@/features/map-chat/analysis/chat-analysis-card"
import { applyChatEvent } from "@/features/map-chat/chat-events"
import { historyContent } from "@/features/map-chat/chat-history"
import { isChatAnalysis } from "@/shared/api/chat-analysis"
import { streamChat } from "@/shared/api/chat-stream"
import type { AnalysisJob } from "@/shared/api/road-analysis"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/chat.json"

vi.mock("@/shared/api/chat-stream", async (load) => ({
  ...(await load<typeof import("@/shared/api/chat-stream")>()),
  streamChat: vi.fn(),
}))

const analysis: AnalysisJob = {
  id: "analysis-1",
  region_id: "16",
  region: "Region",
  mode: "improvement",
  percent: 20,
  fingerprint: "snapshot",
  status: "running",
  stage: "verifying",
  candidates: [],
  results: [],
  failures: [],
  candidate_count: 25,
  batch_target: 10,
  current_way_id: 1,
  completed: 5,
  total: 20,
  elapsed_seconds: 1,
  error: null,
  compatible: true,
}
const completed: AnalysisJob = {
  ...analysis,
  status: "paused",
  results: [1, 2].map((id) => ({
    candidate: {
      way_id: id,
      name: `Road ${id}`,
      length_km: 4,
      score: 1,
      isolation_score: 0,
      crosses_boundary: false,
    },
    before: 100,
    after: 100 + id,
    delta: id,
    affected_population: 100 * id,
    isolated_population: 0,
    elapsed_seconds: 1,
  })),
}
const clients: QueryClient[] = []
function setup(job = analysis, commentary?: AnalysisCommentary) {
  const client = new QueryClient({
    defaultOptions: { queries: { staleTime: Infinity, retry: false } },
  })
  clients.push(client)
  const view = render(
    <QueryClientProvider client={client}>
      <LocaleProvider>
        <ChatAnalysisCard analysis={job} commentary={commentary} />
      </LocaleProvider>
    </QueryClientProvider>,
  )
  return { client, ...view }
}

afterEach(() => {
  clients.splice(0).forEach((client) => {
    client.clear()
  })
  vi.resetAllMocks()
})

describe("inline road ranking", () => {
  it("updates the table and automatically streams exactly one commentary when the batch finishes", async () => {
    vi.mocked(streamChat).mockImplementation(async (_body, _signal, emit) => {
      emit({ type: "delta", text: "Result commentary", code: "" })
      emit({ type: "done", text: "", code: "" })
    })
    const { client, unmount } = setup()
    expect(streamChat).not.toHaveBeenCalled()
    expect(screen.getByRole("progressbar")).toBeTruthy()
    act(() => client.setQueryData(["road-analysis", analysis.id], completed))
    await screen.findByText("Result commentary")
    const rows = screen.getAllByRole("row")
    expect(rows[1]?.textContent).toContain("Road 2")
    expect(rows[2]?.textContent).toContain("Road 1")
    expect(streamChat).toHaveBeenCalledTimes(1)
    expect(vi.mocked(streamChat).mock.calls[0]?.[0].analysis_id).toBe(analysis.id)
    act(() =>
      client.setQueryData(["road-analysis", analysis.id], { ...completed, elapsed_seconds: 40 }),
    )
    expect(streamChat).toHaveBeenCalledTimes(1)
    expect(screen.queryByRole("link")).toBeNull()
    unmount()
  })

  it("keeps verified rows when commentary fails and retries only the commentary", async () => {
    vi.mocked(streamChat).mockRejectedValueOnce(new Error("offline"))
    const { unmount } = setup(completed)
    await screen.findByRole("button", { name: ru.retry })
    expect(screen.getByRole("table")).toBeTruthy()
    vi.mocked(streamChat).mockImplementation(async (_body, _signal, emit) => {
      emit({ type: "delta", text: "Recovered commentary", code: "" })
      emit({ type: "done", text: "", code: "" })
    })
    fireEvent.click(screen.getByRole("button", { name: ru.retry }))
    await screen.findByText("Recovered commentary")
    expect(streamChat).toHaveBeenCalledTimes(2)
    unmount()
  })

  it("does not describe a failed calculation as a completed analysis", async () => {
    const { unmount } = setup({ ...completed, status: "failed" })
    await waitFor(() => expect(screen.getByRole("table")).toBeTruthy())
    expect(streamChat).not.toHaveBeenCalled()
    unmount()
  })

  it("restores saved commentary without another model request", async () => {
    const { unmount } = setup(completed, {
      revision: "10:2:0",
      text: "Saved commentary",
      complete: true,
      error: null,
    })
    await screen.findByText("Saved commentary")
    expect(streamChat).not.toHaveBeenCalled()
    unmount()
  })

  it("preserves analysis references and rejects malformed numerical results", () => {
    expect(isChatAnalysis(completed)).toBe(true)
    expect(isChatAnalysis({ ...completed, results: [{ delta: "invented" }] })).toBe(false)
    const entry = {
      id: "answer",
      role: "assistant" as const,
      content: "",
      complete: true,
      steps: [],
      tables: [],
      charts: [],
      mapCommands: [],
    }
    const event = { type: "analysis" as const, text: "", code: "", analysis }
    const updated = applyChatEvent(applyChatEvent(entry, event), event)
    expect(updated.analyses).toHaveLength(1)
    expect(historyContent(updated)).toContain(analysis.id)
  })
})
