import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { useState } from "react"
import { describe, expect, it } from "vitest"
import common from "@/shared/i18n/locales/ru/common.json"
import { Button, Dialog, Sheet } from "@/shared/ui"
import { text as home } from "./dictionary-text"

function Probe({ sheet = false }: { readonly sheet?: boolean }) {
  const [open, setOpen] = useState(false)
  const Overlay = sheet ? Sheet : Dialog
  return (
    <>
      <Button onClick={() => setOpen(true)}>{home.formats.title}</Button>
      <Overlay
        open={open}
        onClose={() => setOpen(false)}
        title={home.empty.title}
        description={home.empty.description}
        actions={<Button onClick={() => setOpen(false)}>{common.action.retry}</Button>}
      >
        {home.description}
      </Overlay>
    </>
  )
}

const opener = () => screen.getByRole("button", { name: home.formats.title })

async function openDialog() {
  await userEvent.click(opener())
  return screen.getByRole("dialog", { name: home.empty.title })
}

describe("Dialog", () => {
  it("is a named modal dialog with its title focused", async () => {
    render(<Probe />)
    const dialog = await openDialog()
    expect(dialog.getAttribute("aria-modal")).toBe("true")
    expect(dialog.getAttribute("aria-describedby")).toBe(
      screen.getByText(home.empty.description).id,
    )
    expect(document.activeElement).toBe(screen.getByRole("heading", { name: home.empty.title }))
  })

  it("keeps Tab and Shift+Tab inside the dialog", async () => {
    render(<Probe />)
    await openDialog()
    const close = screen.getByRole("button", { name: common.ui.close })
    const action = screen.getByRole("button", { name: common.action.retry })
    await userEvent.tab()
    expect(document.activeElement).toBe(close)
    fireEvent.keyDown(close, { key: "Tab", shiftKey: true })
    expect(document.activeElement).toBe(action)
    fireEvent.keyDown(action, { key: "Tab" })
    expect(document.activeElement).toBe(close)
  })

  it("closes on Escape and returns focus to the opener", async () => {
    render(<Probe />)
    await openDialog()
    await userEvent.keyboard("{Escape}")
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull())
    expect(document.activeElement).toBe(opener())
  })

  it("closes from the close button named from the dictionary", async () => {
    render(<Probe />)
    await openDialog()
    await userEvent.click(screen.getByRole("button", { name: common.ui.close }))
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull())
  })
})

describe("Sheet", () => {
  it("shares the modal behaviour of the dialog", async () => {
    render(<Probe sheet />)
    await openDialog()
    expect(document.activeElement).toBe(screen.getByRole("heading", { name: home.empty.title }))
    await userEvent.keyboard("{Escape}")
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull())
    expect(document.activeElement).toBe(opener())
  })
})
