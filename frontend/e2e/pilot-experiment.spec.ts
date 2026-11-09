import { readFile } from "node:fs/promises"
import AxeBuilder from "@axe-core/playwright"
import { expect, test } from "@playwright/test"
import type { components } from "../src/shared/api/schema.gen"
import copy from "../src/shared/i18n/locales/ru/pilot.json" with { type: "json" }

test("map to pilot, evaluate frequency, export and reset", async ({ page, request }) => {
  const pilot: components["schemas"]["PilotResponse"] = await (
    await request.get("/api/v1/pilots/tuva")
  ).json()
  const origin = pilot.points.find((point) => point.id === "93643425101")?.name ?? ""
  await page.goto("/map?region=93000000&season=summer")
  await page.getByRole("link", { name: copy.open, exact: true }).click()
  await expect(page.getByRole("heading", { name: copy.title, exact: true })).toBeVisible()
  const frequency = page.getByRole("textbox", { name: copy.frequency, exact: true }).first()
  await frequency.fill("7")
  await page.getByRole("button", { name: copy.calculate, exact: true }).click()
  const result = page.getByRole("article").filter({ hasText: origin })
  await expect(result.getByText("14,24", { exact: true })).toBeVisible()
  await expect(result.getByText(/[-−]3,85$/)).toBeVisible()
  await page.screenshot({ path: "test-results/pilot-results-desktop.png", fullPage: false })
  await frequency.fill("4")
  await expect(page.getByText(copy.stale, { exact: true })).toBeVisible()
  const downloadEvent = page.waitForEvent("download")
  await page.getByRole("button", { name: copy.json, exact: true }).click()
  const download = await downloadEvent
  const path = await download.path()
  expect(path).not.toBeNull()
  const exported = JSON.parse(await readFile(path ?? "", "utf8"))
  expect(exported.evaluation.changes[0].frequency_per_week).toBe(7)
  const csvEvent = page.waitForEvent("download")
  await page.getByRole("button", { name: copy.csv, exact: true }).click()
  expect((await csvEvent).suggestedFilename()).toBe("plexus-comparison.csv")
  await page.getByRole("button", { name: copy.calculate, exact: true }).click()
  await expect(page.getByText(copy.stale, { exact: true })).toHaveCount(0)
  await expect(
    result.getByRole("row").filter({ hasText: copy.changed }).getByRole("cell").nth(1),
  ).toHaveText("18,10")
  await page.getByRole("button", { name: copy.reset, exact: true }).click()
  await expect(frequency).toHaveValue("2")
  await expect(page.getByText(copy.empty, { exact: true })).toBeVisible()
  await page.screenshot({ path: "test-results/pilot-desktop.png", fullPage: true })
  const accessibility = await new AxeBuilder({ page }).analyze()
  expect(accessibility.violations).toEqual([])
})
