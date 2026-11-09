import { act, fireEvent, render, screen } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import common from "@/shared/i18n/locales/ru/common.json"
import { Combobox, type ComboboxGroup } from "@/shared/ui"
import { applyMotionTokens } from "../../setup/motionEnvironment"
import { text as home } from "./dictionary-text"

const GROUPS: readonly ComboboxGroup[] = [
  {
    key: "formats",
    label: home.formats.title,
    items: [
      { value: "number", label: home.formats.number },
      { value: "money", label: home.formats.money, meta: home.formats.count },
    ],
  },
  {
    key: "empty",
    label: home.empty.title,
    items: [{ value: "date", label: home.formats.date, icon: "calendar" }],
  },
]

interface ProbeProps {
  readonly groups?: readonly ComboboxGroup[]
  readonly loading?: boolean
  readonly onQuery?: (query: string) => void
  readonly onSelect?: (value: string) => void
}

function Probe({ groups = GROUPS, loading = false, onQuery, onSelect }: ProbeProps) {
  return (
    <Combobox
      label={home.title}
      groups={groups}
      loading={loading}
      onQuery={(query) => onQuery?.(query)}
      onSelect={(item) => onSelect?.(item.value)}
    />
  )
}

const input = () => screen.getByRole("combobox", { name: home.title })
const type = (value: string) => fireEvent.change(input(), { target: { value } })
const press = (...keys: readonly string[]) => {
  for (const key of keys) fireEvent.keyDown(input(), { key })
}

describe("Combobox", () => {
  beforeEach(() => {
    vi.useFakeTimers()
    applyMotionTokens()
  })
  afterEach(() => vi.useRealTimers())

  it("debounces onQuery and calls it once with the final text", () => {
    const onQuery = vi.fn()
    render(<Probe onQuery={onQuery} />)
    type(home.formats.number)
    type(home.formats.money)
    expect(onQuery).not.toHaveBeenCalled()
    act(() => vi.advanceTimersByTime(250))
    expect(onQuery).toHaveBeenCalledOnce()
    expect(onQuery).toHaveBeenCalledWith(home.formats.money)
  })

  it("renders suggestions in named groups and follows the combobox pattern", () => {
    render(<Probe />)
    type(home.formats.money.charAt(0))
    expect(input().getAttribute("aria-expanded")).toBe("true")
    expect(input().getAttribute("aria-autocomplete")).toBe("list")
    const listbox = screen.getByRole("listbox", { name: home.title })
    expect(input().getAttribute("aria-controls")).toBe(listbox.id)
    const group = screen.getByRole("group", { name: home.empty.title })
    expect(group.textContent).toContain(home.formats.date)
  })

  it("moves the active option with arrows and selects with Enter", () => {
    const onSelect = vi.fn()
    render(<Probe onSelect={onSelect} />)
    type(home.formats.money.charAt(0))
    press("ArrowDown")
    const first = screen.getByRole("option", { name: home.formats.number })
    expect(input().getAttribute("aria-activedescendant")).toBe(first.id)
    expect(first.getAttribute("aria-selected")).toBe("true")
    press("ArrowDown", "ArrowDown", "ArrowDown")
    const last = screen.getByRole("option", { name: home.formats.date })
    expect(input().getAttribute("aria-activedescendant")).toBe(last.id)
    press("ArrowUp", "Enter")
    expect(onSelect).toHaveBeenCalledWith("money")
    expect((input() as HTMLInputElement).value).toBe(home.formats.money)
    expect(input().getAttribute("aria-expanded")).toBe("false")
  })

  it("closes on the first Escape and clears the text on the second", () => {
    render(<Probe />)
    type(home.formats.money.charAt(0))
    press("Escape")
    expect(input().getAttribute("aria-expanded")).toBe("false")
    expect((input() as HTMLInputElement).value).toBe(home.formats.money.charAt(0))
    press("Escape")
    expect((input() as HTMLInputElement).value).toBe("")
  })

  it("shows the empty row once the search settles without results", () => {
    render(<Probe groups={[]} />)
    type(home.formats.money.charAt(0))
    expect(screen.queryByText(common.ui.combobox.empty)).toBeNull()
    act(() => vi.advanceTimersByTime(250))
    expect(screen.getByRole("status").textContent).toBe(common.ui.combobox.empty)
  })

  it("shows the loading row only after the indicator delay", () => {
    render(<Probe groups={[]} loading />)
    type(home.formats.money.charAt(0))
    act(() => vi.advanceTimersByTime(100))
    expect(screen.queryByText(common.ui.combobox.loading)).toBeNull()
    act(() => vi.advanceTimersByTime(200))
    expect(screen.getByText(common.ui.combobox.loading)).toBeTruthy()
  })
})
