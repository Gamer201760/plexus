import { fireEvent, render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import { AnalysisProgress } from "@/features/road-analysis/analysis-progress"
import { AnalysisRanking } from "@/features/road-analysis/analysis-ranking"
import type { AnalysisJob, VerifiedRoad } from "@/shared/api/road-analysis"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/analysis.json"

function road(id: number, delta: number, isolated: number): VerifiedRoad {
  return {
    candidate: {
      way_id: id,
      name: `Road ${id}`,
      length_km: 4,
      score: 0,
      isolation_score: 0,
      crosses_boundary: false,
    },
    before: 100,
    after: 100 + delta,
    delta,
    affected_population: 100,
    isolated_population: isolated,
    elapsed_seconds: 1,
  }
}

function job(results: VerifiedRoad[]): AnalysisJob {
  return {
    id: "job",
    region_id: "1",
    region: "Region",
    mode: "criticality",
    percent: 0,
    fingerprint: "source",
    status: "paused",
    stage: "batch_complete",
    candidates: [],
    results,
    failures: [],
    candidate_count: 20,
    batch_target: 10,
    current_way_id: null,
    completed: 180,
    total: 180,
    elapsed_seconds: 1,
    error: null,
    compatible: true,
  }
}

describe("road analysis", () => {
  it("keeps isolation and accessibility as independent rankings", () => {
    render(
      <LocaleProvider>
        <AnalysisRanking
          job={job([road(1, -10, 0), road(2, -1, 100)])}
          selectedWay={null}
          onSelect={vi.fn()}
        />
      </LocaleProvider>,
    )
    expect(screen.getAllByRole("listitem")[0]?.textContent).toContain("Road 1")
    fireEvent.click(screen.getByRole("radio", { name: ru.isolationRanking }))
    expect(screen.getAllByRole("listitem")[0]?.textContent).toContain("Road 2")
  })

  it("does not move a row while the user reads it", () => {
    const onSelect = vi.fn()
    const result = render(
      <LocaleProvider>
        <AnalysisRanking job={job([road(1, -1, 0)])} selectedWay={null} onSelect={onSelect} />
      </LocaleProvider>,
    )
    fireEvent.focus(screen.getByRole("button", { name: "Road 1" }))
    result.rerender(
      <LocaleProvider>
        <AnalysisRanking
          job={job([road(1, -1, 0), road(2, -10, 0)])}
          selectedWay={null}
          onSelect={onSelect}
        />
      </LocaleProvider>,
    )
    expect(screen.getAllByRole("listitem")[0]?.textContent).toContain("Road 1")
    fireEvent.click(screen.getByRole("button", { name: ru.reorder }))
    expect(screen.getAllByRole("listitem")[0]?.textContent).toContain("Road 2")
  })

  it("cannot continue incompatible saved results", () => {
    render(
      <LocaleProvider>
        <AnalysisProgress
          job={{ ...job([]), compatible: false }}
          busy={false}
          pending={false}
          control={vi.fn()}
        />
      </LocaleProvider>,
    )
    expect(screen.queryByRole("button", { name: ru.continue })).toBeNull()
    expect(screen.getByText(ru.incompatible)).toBeTruthy()
  })

  it("cancels only through the explicit action", () => {
    const control = vi.fn()
    render(
      <LocaleProvider>
        <AnalysisProgress
          job={{ ...job([]), status: "running", stage: "verifying", completed: 5 }}
          busy
          pending={false}
          control={control}
        />
      </LocaleProvider>,
    )
    expect(screen.getByRole("progressbar").getAttribute("value")).toBe("5")
    fireEvent.click(screen.getByRole("button", { name: ru.stop }))
    expect(control).toHaveBeenCalledWith("cancel")
  })
})
