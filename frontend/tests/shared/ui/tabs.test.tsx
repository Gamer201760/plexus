import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { useState } from "react"
import { describe, expect, it } from "vitest"
import { type TabItem, Tabs } from "@/shared/ui"
import { text as home } from "./dictionary-text"

type Section = "number" | "money" | "date"

const ITEMS: readonly TabItem<Section>[] = [
  { value: "number", label: home.formats.number },
  { value: "money", label: home.formats.money },
  { value: "date", label: home.formats.date, icon: "calendar" },
]

const PANELS: Readonly<Record<Section, string>> = {
  number: home.formats.count,
  money: home.formats.percent,
  date: home.formats.missing,
}

function Probe() {
  const [value, setValue] = useState<Section>("number")
  return (
    <Tabs label={home.formats.title} items={ITEMS} value={value} onChange={setValue}>
      {PANELS[value]}
    </Tabs>
  )
}

const tab = (name: string) => screen.getByRole("tab", { name })

describe("Tabs", () => {
  it("exposes a named tablist with one tab in the tab order", () => {
    render(<Probe />)
    expect(screen.getByRole("tablist", { name: home.formats.title })).toBeTruthy()
    expect(tab(home.formats.number).getAttribute("aria-selected")).toBe("true")
    expect(tab(home.formats.number).tabIndex).toBe(0)
    expect(tab(home.formats.money).tabIndex).toBe(-1)
    const panel = screen.getByRole("tabpanel", { name: home.formats.number })
    expect(tab(home.formats.number).getAttribute("aria-controls")).toBe(panel.id)
  })

  it("moves selection and focus with arrows, wrapping at the ends", async () => {
    render(<Probe />)
    await userEvent.tab()
    expect(document.activeElement).toBe(tab(home.formats.number))
    await userEvent.keyboard("{ArrowRight}")
    expect(tab(home.formats.money).getAttribute("aria-selected")).toBe("true")
    expect(document.activeElement).toBe(tab(home.formats.money))
    await userEvent.keyboard("{ArrowLeft}{ArrowLeft}")
    expect(document.activeElement).toBe(tab(home.formats.date))
    await userEvent.keyboard("{ArrowRight}")
    expect(document.activeElement).toBe(tab(home.formats.number))
  })

  it("jumps with Home and End", async () => {
    render(<Probe />)
    await userEvent.tab()
    await userEvent.keyboard("{End}")
    expect(tab(home.formats.date).getAttribute("aria-selected")).toBe("true")
    await userEvent.keyboard("{Home}")
    expect(tab(home.formats.number).getAttribute("aria-selected")).toBe("true")
  })

  it("selects a tab on click and labels the panel with it", async () => {
    render(<Probe />)
    await userEvent.click(tab(home.formats.money))
    expect(screen.getByRole("tabpanel", { name: home.formats.money })).toBeTruthy()
  })
})
