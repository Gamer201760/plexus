import { act, fireEvent, render, screen } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import common from "@/shared/i18n/locales/ru/common.json"
import errors from "@/shared/i18n/locales/ru/errors.json"
import { Button, type StatusTone, ToastHost, useToast } from "@/shared/ui"
import { applyMotionTokens } from "../../setup/motionEnvironment"
import { text as home } from "./dictionary-text"

function Trigger({ tone, title }: { readonly tone: StatusTone; readonly title: string }) {
  const { notify } = useToast()
  return <Button onClick={() => notify({ tone, title })}>{home.formats.title}</Button>
}

function renderHost(tone: StatusTone, title: string) {
  render(
    <ToastHost>
      <Trigger tone={tone} title={title} />
    </ToastHost>,
  )
  fireEvent.click(screen.getByRole("button", { name: home.formats.title }))
}

const advance = (ms: number) => act(() => vi.advanceTimersByTime(ms))
const region = () => screen.getByRole("region", { name: common.ui.toast.region })

describe("Toast", () => {
  beforeEach(() => {
    vi.useFakeTimers()
    applyMotionTokens()
  })
  afterEach(() => vi.useRealTimers())

  it("announces in a polite live region and leaves after five seconds", () => {
    renderHost("success", home.empty.title)
    expect(region().querySelector("ol")?.getAttribute("aria-live")).toBe("polite")
    expect(screen.getByText(home.empty.title)).toBeTruthy()
    advance(4900)
    expect(screen.getByText(home.empty.title)).toBeTruthy()
    advance(100)
    advance(300)
    expect(screen.queryByText(home.empty.title)).toBeNull()
  })

  it("keeps errors as alerts for ten seconds", () => {
    renderHost("danger", errors.kind.server)
    expect(screen.getByRole("alert").textContent).toContain(errors.kind.server)
    advance(6000)
    expect(screen.getByRole("alert")).toBeTruthy()
    advance(4000)
    advance(300)
    expect(screen.queryByRole("alert")).toBeNull()
  })

  it("pauses while hovered and resumes with the remaining time", () => {
    renderHost("info", home.empty.title)
    advance(2000)
    fireEvent.pointerEnter(region())
    advance(8000)
    expect(screen.getByText(home.empty.title)).toBeTruthy()
    fireEvent.pointerLeave(region())
    advance(3000)
    advance(300)
    expect(screen.queryByText(home.empty.title)).toBeNull()
  })

  it("closes from its close button", () => {
    renderHost("warning", home.empty.title)
    fireEvent.click(screen.getByRole("button", { name: common.ui.close }))
    advance(300)
    expect(screen.queryByText(home.empty.title)).toBeNull()
  })
})
