import { expect, test } from "@playwright/test"
import commonCopy from "../src/shared/i18n/locales/ru/common.json" with { type: "json" }
import pilotCopy from "../src/shared/i18n/locales/ru/pilot.json" with { type: "json" }

test("pilot calculation can be retried after a temporary server error", async ({ page }) => {
  await page.goto("/pilot")
  const frequency = page.getByRole("textbox", { name: pilotCopy.frequency, exact: true }).first()
  await frequency.fill("7")
  await page.route("**/api/v1/pilots/tuva/evaluate", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ code: "data_unavailable", message: "Pilot unavailable" }),
    }),
  )
  await page.getByRole("button", { name: pilotCopy.calculate, exact: true }).click()
  await expect(page.getByText(pilotCopy.errors.title, { exact: true })).toBeVisible()
  await expect(page.getByText("14,24", { exact: true })).toHaveCount(0)
  await page.unroute("**/api/v1/pilots/tuva/evaluate")
  await page.getByRole("button", { name: commonCopy.action.retry, exact: true }).click()
  await expect(page.getByText("14,24", { exact: true }).first()).toBeVisible()
  await expect(page.getByText(pilotCopy.errors.title, { exact: true })).toHaveCount(0)
  await expect(frequency).toHaveValue("7")
})

test("failed recalculation cannot present the previous result as current", async ({ page }) => {
  await page.goto("/pilot")
  const frequency = page.getByRole("textbox", { name: pilotCopy.frequency, exact: true }).first()
  const calculate = page.getByRole("button", { name: pilotCopy.calculate, exact: true })
  await frequency.fill("7")
  await calculate.click()
  await expect(page.getByText("14,24", { exact: true }).first()).toBeVisible()
  await frequency.fill("4")
  await expect(page.getByText(pilotCopy.stale, { exact: true })).toBeVisible()
  await page.route("**/api/v1/pilots/tuva/evaluate", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ code: "data_unavailable", message: "Pilot unavailable" }),
    }),
  )
  await calculate.click()
  await expect(page.getByText(pilotCopy.errors.title, { exact: true })).toBeVisible()
  await expect(page.getByText("14,24", { exact: true })).toHaveCount(0)
  await page.unroute("**/api/v1/pilots/tuva/evaluate")
  const response = page.waitForResponse("**/api/v1/pilots/tuva/evaluate")
  await page.getByRole("button", { name: commonCopy.action.retry, exact: true }).click()
  const retried = await response
  expect(retried.request().postDataJSON().changes[0].frequency_per_week).toBe(4)
  expect((await retried.json()).pairs[0].changed.total_h).toBeCloseTo(18.0951, 3)
  await expect(page.getByText(pilotCopy.errors.title, { exact: true })).toHaveCount(0)
  await expect(page.getByText(pilotCopy.stale, { exact: true })).toHaveCount(0)
  await expect(page.getByText("18,10", { exact: true }).first()).toBeVisible()
  await expect(frequency).toHaveValue("4")
})

test("stale pilot version reloads data before a new calculation", async ({ page }) => {
  await page.route("**/api/v1/pilots/tuva", async (route) => {
    const original = await route.fetch()
    const pilot = await original.json()
    pilot.artifact_version = "outdated-test-version"
    await route.fulfill({ response: original, json: pilot })
  })
  await page.goto("/pilot")
  const frequency = page.getByRole("textbox", { name: pilotCopy.frequency, exact: true }).first()
  await frequency.fill("7")
  const failed = page.waitForResponse("**/api/v1/pilots/tuva/evaluate")
  await page.getByRole("button", { name: pilotCopy.calculate, exact: true }).click()
  expect((await failed).status()).toBe(409)
  await expect(page.getByText(pilotCopy.errors.title, { exact: true })).toBeVisible()
  await page.unroute("**/api/v1/pilots/tuva")
  const refreshed = page.waitForResponse("**/api/v1/pilots/tuva")
  await page.getByRole("button", { name: commonCopy.action.retry, exact: true }).click()
  expect((await refreshed).status()).toBe(200)
  await expect(page.getByText(pilotCopy.errors.title, { exact: true })).toHaveCount(0)
  await expect(frequency).toHaveValue("2")
  await frequency.fill("7")
  await page.getByRole("button", { name: pilotCopy.calculate, exact: true }).click()
  await expect(page.getByText("14,24", { exact: true }).first()).toBeVisible()
})

test("successful same-version reload clears a stale-version error", async ({ page }) => {
  await page.goto("/pilot")
  const frequency = page.getByRole("textbox", { name: pilotCopy.frequency, exact: true }).first()
  await frequency.fill("7")
  await page.route(
    "**/api/v1/pilots/tuva/evaluate",
    (route) =>
      route.fulfill({
        status: 409,
        contentType: "application/json",
        body: JSON.stringify({ code: "stale_pilot_version", message: "Stale pilot" }),
      }),
    { times: 1 },
  )
  await page.getByRole("button", { name: pilotCopy.calculate, exact: true }).click()
  await expect(page.getByText(pilotCopy.errors.title, { exact: true })).toBeVisible()
  const refreshed = page.waitForResponse("**/api/v1/pilots/tuva")
  await page.getByRole("button", { name: commonCopy.action.retry, exact: true }).click()
  expect((await refreshed).status()).toBe(200)
  await expect(page.getByText(pilotCopy.errors.title, { exact: true })).toHaveCount(0)
  await expect(frequency).toHaveValue("7")
  await page.getByRole("button", { name: pilotCopy.calculate, exact: true }).click()
  await expect(page.getByText("14,24", { exact: true }).first()).toBeVisible()
})

test("failed pilot reload keeps the version error visible", async ({ page }) => {
  await page.goto("/pilot")
  const frequency = page.getByRole("textbox", { name: pilotCopy.frequency, exact: true }).first()
  await frequency.fill("7")
  await page.route(
    "**/api/v1/pilots/tuva/evaluate",
    (route) =>
      route.fulfill({
        status: 409,
        contentType: "application/json",
        body: JSON.stringify({ code: "stale_pilot_version", message: "Stale pilot" }),
      }),
    { times: 1 },
  )
  await page.getByRole("button", { name: pilotCopy.calculate, exact: true }).click()
  await expect(page.getByText(pilotCopy.errors.title, { exact: true })).toBeVisible()
  await page.route("**/api/v1/pilots/tuva", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ code: "data_unavailable", message: "Pilot unavailable" }),
    }),
  )
  const failed = page.waitForResponse("**/api/v1/pilots/tuva")
  await page.getByRole("button", { name: commonCopy.action.retry, exact: true }).click()
  expect((await failed).status()).toBe(503)
  await expect(page.getByText(pilotCopy.errors.title, { exact: true })).toBeVisible()
  await expect(frequency).toHaveValue("7")
})

test("late pilot reload does not erase a newer calculation", async ({ page }) => {
  await page.goto("/pilot")
  const frequency = page.getByRole("textbox", { name: pilotCopy.frequency, exact: true }).first()
  await frequency.fill("7")
  await page.route(
    "**/api/v1/pilots/tuva/evaluate",
    (route) =>
      route.fulfill({
        status: 409,
        contentType: "application/json",
        body: JSON.stringify({ code: "stale_pilot_version", message: "Stale pilot" }),
      }),
    { times: 1 },
  )
  const calculate = page.getByRole("button", { name: pilotCopy.calculate, exact: true })
  await calculate.click()
  await expect(page.getByText(pilotCopy.errors.title, { exact: true })).toBeVisible()
  let release = () => {}
  let observed = () => {}
  const pending = new Promise<void>((resolve) => {
    release = resolve
  })
  const received = new Promise<void>((resolve) => {
    observed = resolve
  })
  await page.route("**/api/v1/pilots/tuva", async (route) => {
    observed()
    await pending
    await route.continue()
  })
  await page.getByRole("button", { name: commonCopy.action.retry, exact: true }).click()
  await received
  await calculate.click()
  await expect(page.getByText("14,24", { exact: true }).first()).toBeVisible()
  const refreshed = page.waitForResponse("**/api/v1/pilots/tuva")
  release()
  expect((await refreshed).status()).toBe(200)
  await page.evaluate(
    () =>
      new Promise<void>((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
      ),
  )
  await expect(page.getByText("14,24", { exact: true }).first()).toBeVisible()
  await expect(page.getByText(pilotCopy.errors.title, { exact: true })).toHaveCount(0)
})
