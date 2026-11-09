import { expect, test } from "@playwright/test"
import copy from "../src/shared/i18n/locales/ru/pilot.json" with { type: "json" }

test("editing during a pending calculation marks its eventual result stale", async ({ page }) => {
  let release = () => {}
  let observed = () => {}
  const pending = new Promise<void>((resolve) => {
    release = resolve
  })
  const received = new Promise<void>((resolve) => {
    observed = resolve
  })
  await page.route("**/api/v1/pilots/tuva/evaluate", async (route) => {
    observed()
    await pending
    await route.continue()
  })
  await page.goto("/pilot")
  const frequency = page.getByRole("textbox", { name: copy.frequency, exact: true }).first()
  await frequency.fill("7")
  await page.getByRole("button", { name: copy.calculate, exact: true }).click()
  await received
  await frequency.fill("4")
  release()
  await expect(page.getByText(copy.stale, { exact: true })).toBeVisible()
  await expect(page.getByText("14,24", { exact: true }).first()).toBeVisible()
})

test("reset prevents a pending result from reappearing", async ({ page }) => {
  let release = () => {}
  let observed = () => {}
  const pending = new Promise<void>((resolve) => {
    release = resolve
  })
  const received = new Promise<void>((resolve) => {
    observed = resolve
  })
  await page.route("**/api/v1/pilots/tuva/evaluate", async (route) => {
    observed()
    await pending
    await route.continue()
  })
  await page.goto("/pilot")
  const frequency = page.getByRole("textbox", { name: copy.frequency, exact: true }).first()
  await frequency.fill("7")
  await page.getByRole("button", { name: copy.calculate, exact: true }).click()
  await received
  await page.getByRole("button", { name: copy.reset, exact: true }).click()
  const response = page.waitForResponse("**/api/v1/pilots/tuva/evaluate")
  release()
  await response
  await expect(page.getByText(copy.empty, { exact: true })).toBeVisible()
  await expect(page.getByText("14,24", { exact: true })).toHaveCount(0)
})

test("reset prevents a late error from an abandoned calculation", async ({ page }) => {
  let release = () => {}
  let observed = () => {}
  const pending = new Promise<void>((resolve) => {
    release = resolve
  })
  const received = new Promise<void>((resolve) => {
    observed = resolve
  })
  await page.route("**/api/v1/pilots/tuva/evaluate", async (route) => {
    observed()
    await pending
    await route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ code: "data_unavailable", message: "Pilot unavailable" }),
    })
  })
  await page.goto("/pilot")
  const frequency = page.getByRole("textbox", { name: copy.frequency, exact: true }).first()
  await frequency.fill("7")
  await page.getByRole("button", { name: copy.calculate, exact: true }).click()
  await received
  await page.getByRole("button", { name: copy.reset, exact: true }).click()
  const response = page.waitForResponse("**/api/v1/pilots/tuva/evaluate")
  release()
  expect((await response).status()).toBe(503)
  await page.unroute("**/api/v1/pilots/tuva/evaluate")
  await expect(page.getByText(copy.empty, { exact: true })).toBeVisible()
  await expect(page.getByText(copy.errors.title, { exact: true })).toHaveCount(0)
  await expect(frequency).toHaveValue("2")
  await page.getByRole("button", { name: copy.calculate, exact: true }).click()
  await expect(page.getByText("18,10", { exact: true }).first()).toBeVisible()
})
