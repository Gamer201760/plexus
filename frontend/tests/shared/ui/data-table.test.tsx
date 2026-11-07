import { render, screen, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"
import { DataTable, type DataTableColumn } from "@/shared/ui"
import { text as home } from "./dictionary-text"

interface Row {
  readonly id: string
  readonly name: string
  readonly amount: number
}

const ROWS: readonly Row[] = [
  { id: "a", name: home.formats.number, amount: 3 },
  { id: "b", name: home.formats.percent, amount: 10 },
  { id: "c", name: home.formats.money, amount: 2 },
]

const COLUMNS: readonly DataTableColumn<Row>[] = [
  {
    key: "name",
    header: home.formats.title,
    cell: (row) => row.name,
    sortValue: (row) => row.name,
  },
  {
    key: "amount",
    header: home.formats.count,
    cell: (row) => row.amount,
    numeric: true,
    sortValue: (row) => row.amount,
  },
]

const header = (name: string) => screen.getByRole("columnheader", { name })
const firstColumn = () =>
  screen
    .getAllByRole("row")
    .slice(1)
    .map((row) => within(row).getAllByRole("cell")[0]?.textContent)

describe("DataTable", () => {
  it("renders a captioned table inside a keyboard scrollable region", () => {
    render(
      <DataTable caption={home.title} columns={COLUMNS} rows={ROWS} rowKey={(row) => row.id} />,
    )
    const region = screen.getByRole("region", { name: home.title })
    expect(region.tabIndex).toBe(0)
    expect(within(region).getByRole("table", { name: home.title })).toBeTruthy()
    expect(header(home.formats.count).className).toContain("numeric")
  })

  it("sorts numeric columns descending first and toggles with aria-sort", async () => {
    const onSortChange = vi.fn()
    render(
      <DataTable
        caption={home.title}
        columns={COLUMNS}
        rows={ROWS}
        rowKey={(row) => row.id}
        onSortChange={onSortChange}
      />,
    )
    expect(header(home.formats.count).getAttribute("aria-sort")).toBe("none")
    await userEvent.click(screen.getByRole("button", { name: home.formats.count }))
    expect(header(home.formats.count).getAttribute("aria-sort")).toBe("descending")
    expect(onSortChange).toHaveBeenLastCalledWith({ key: "amount", direction: "descending" })
    expect(firstColumn()).toEqual([home.formats.percent, home.formats.number, home.formats.money])
    await userEvent.click(screen.getByRole("button", { name: home.formats.count }))
    expect(header(home.formats.count).getAttribute("aria-sort")).toBe("ascending")
    expect(firstColumn()).toEqual([home.formats.money, home.formats.number, home.formats.percent])
  })

  it("sorts text columns ascending first with the russian collation", async () => {
    render(
      <DataTable caption={home.title} columns={COLUMNS} rows={ROWS} rowKey={(row) => row.id} />,
    )
    await userEvent.click(screen.getByRole("button", { name: home.formats.title }))
    expect(header(home.formats.title).getAttribute("aria-sort")).toBe("ascending")
    expect(header(home.formats.count).getAttribute("aria-sort")).toBe("none")
    const expected = [...ROWS.map((row) => row.name)].sort((a, b) => a.localeCompare(b, "ru"))
    expect(firstColumn()).toEqual(expected)
  })

  it("opens a row from the keyboard through its first cell button", async () => {
    const onRowClick = vi.fn()
    render(
      <DataTable
        caption={home.title}
        columns={COLUMNS}
        rows={ROWS}
        rowKey={(row) => row.id}
        onRowClick={onRowClick}
        selectedKey="b"
      />,
    )
    screen.getByRole("button", { name: home.formats.money }).focus()
    await userEvent.keyboard("{Enter}")
    expect(onRowClick).toHaveBeenCalledWith(ROWS[2])
    const selected = screen.getAllByRole("row").find((row) => row.getAttribute("aria-current"))
    expect(selected?.textContent).toContain(home.formats.percent)
  })
})
