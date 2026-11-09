import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { useState } from "react"
import { describe, expect, it, vi } from "vitest"
import common from "@/shared/i18n/locales/ru/common.json"
import { Select, type SelectOption } from "@/shared/ui"
import { text as home } from "./dictionary-text"

type Format = "number" | "percent" | "money" | "date"

const OPTIONS: readonly SelectOption<Format>[] = [
  { value: "number", label: home.formats.number, icon: "list" },
  { value: "percent", label: home.formats.percent, meta: home.formats.count },
  { value: "money", label: home.formats.money },
  { value: "date", label: home.formats.date },
]

function Probe({
  initial,
  onChange,
}: {
  readonly initial: Format | null
  readonly onChange?: (value: Format) => void
}) {
  const [value, setValue] = useState<Format | null>(initial)
  return (
    <Select
      label={home.formats.title}
      options={OPTIONS}
      value={value}
      onChange={(next) => {
        setValue(next)
        onChange?.(next)
      }}
    />
  )
}

const trigger = () => screen.getByRole("combobox", { name: home.formats.title })
const option = (name: string) => screen.getByRole("option", { name })
const activeId = () => trigger().getAttribute("aria-activedescendant")

describe("Select", () => {
  it("shows the dictionary placeholder when nothing is selected", () => {
    render(<Probe initial={null} />)
    expect(trigger().textContent).toContain(common.ui.select.placeholder)
    expect(trigger().getAttribute("aria-haspopup")).toBe("listbox")
  })

  it("opens on ArrowDown at the selected option and marks it as active and selected", async () => {
    render(<Probe initial="percent" />)
    await userEvent.tab()
    await userEvent.keyboard("{ArrowDown}")
    expect(trigger().getAttribute("aria-expanded")).toBe("true")
    expect(screen.getByRole("listbox", { name: home.formats.title })).toBeTruthy()
    expect(activeId()).toBe(option(home.formats.percent).id)
    expect(option(home.formats.percent).getAttribute("aria-selected")).toBe("true")
  })

  it("moves with arrows, Home and End and picks with Enter keeping focus on the trigger", async () => {
    const onChange = vi.fn()
    render(<Probe initial="percent" onChange={onChange} />)
    await userEvent.tab()
    await userEvent.keyboard("{ArrowDown}{ArrowDown}")
    expect(activeId()).toBe(option(home.formats.money).id)
    await userEvent.keyboard("{End}")
    expect(activeId()).toBe(option(home.formats.date).id)
    await userEvent.keyboard("{Home}")
    expect(activeId()).toBe(option(home.formats.number).id)
    await userEvent.keyboard("{Enter}")
    expect(onChange).toHaveBeenCalledWith("number")
    expect(trigger().getAttribute("aria-expanded")).toBe("false")
    expect(trigger().getAttribute("aria-activedescendant")).toBeNull()
    expect(document.activeElement).toBe(trigger())
    expect(trigger().textContent).toContain(home.formats.number)
  })

  it("closes on Escape without changing the value", async () => {
    const onChange = vi.fn()
    render(<Probe initial="money" onChange={onChange} />)
    await userEvent.tab()
    await userEvent.keyboard("{ArrowDown}{ArrowDown}{Escape}")
    expect(trigger().getAttribute("aria-expanded")).toBe("false")
    expect(onChange).not.toHaveBeenCalled()
    await waitFor(() => expect(screen.queryByRole("listbox")).toBeNull())
  })

  it("jumps by typeahead and cycles through options with the same first letter", async () => {
    render(<Probe initial="money" />)
    await userEvent.tab()
    const letter = home.formats.date.charAt(0)
    await userEvent.keyboard(letter)
    expect(activeId()).toBe(option(home.formats.date).id)
    await userEvent.keyboard(letter)
    expect(activeId()).toBe(option(home.formats.percent).id)
  })

  it("picks an option with the pointer", async () => {
    const onChange = vi.fn()
    render(<Probe initial={null} onChange={onChange} />)
    await userEvent.click(trigger())
    await userEvent.click(option(home.formats.money))
    expect(onChange).toHaveBeenCalledWith("money")
    expect(trigger().getAttribute("aria-expanded")).toBe("false")
  })
})
