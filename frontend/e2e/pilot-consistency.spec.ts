import { readFile } from "node:fs/promises"
import { expect, test } from "@playwright/test"
import copy from "../src/shared/i18n/locales/ru/pilot.json" with { type: "json" }

function csvRows(text: string): string[][] {
  return text
    .replace(/^\ufeff/, "")
    .trim()
    .split(/\r?\n/)
    .map((line) => {
      const fields = line.match(/"(?:[^"]|"")*"/g) ?? []
      return fields.map((field) => field.slice(1, -1).replaceAll('""', '"'))
    })
}

test("pilot API, rendered values and exports match submission evidence", async ({ page }) => {
  const pilot = await (await page.request.get("/api/v1/pilots/tuva")).json()
  const origin = pilot.points.find((point: { id: string }) => point.id === "93643425101")
    .name as string
  await page.goto("/pilot")
  const frequency = page.getByRole("textbox", { name: copy.frequency, exact: true }).first()
  await frequency.fill("7")
  const response = page.waitForResponse(
    (r) => r.url().endsWith("/pilots/tuva/evaluate") && r.request().method() === "POST",
  )
  await page.getByRole("button", { name: copy.calculate, exact: true }).click()
  const apiResponse = await response
  expect(apiResponse.status()).toBe(200)
  const api = await apiResponse.json()
  const pair = api.pairs.find((item: { pair_id: string }) => item.pair_id === "kungurtug-kyzyl")
  expect(pair).toBeDefined()
  const article = page.getByRole("article").filter({ hasText: origin })
  const format = (n: number) =>
    new Intl.NumberFormat("ru-RU", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(n)
  await expect(
    article.getByRole("row").filter({ hasText: copy.baseline }).getByRole("cell").nth(1),
  ).toHaveText(format(pair.baseline.total_h))
  await expect(
    article.getByRole("row").filter({ hasText: copy.changed }).getByRole("cell").nth(1),
  ).toHaveText(format(pair.changed.total_h))
  const jsonEvent = page.waitForEvent("download")
  await page.getByRole("button", { name: copy.json, exact: true }).click()
  const jsonDownload = await jsonEvent
  const jsonPath = await jsonDownload.path()
  expect(jsonPath).not.toBeNull()
  const jsonExport = JSON.parse(await readFile(jsonPath ?? "", "utf8"))
  expect(jsonExport.evaluation).toEqual(api)
  const csvEvent = page.waitForEvent("download")
  await page.getByRole("button", { name: copy.csv, exact: true }).click()
  const csvDownload = await csvEvent
  const csvPath = await csvDownload.path()
  expect(csvPath).not.toBeNull()
  const csv = csvRows(await readFile(csvPath ?? "", "utf8"))
  const row = csv.find((cells) => cells[0]?.includes(origin))
  expect(row).toBeDefined()
  expect(Number(row?.[3])).toBeCloseTo(pair.baseline.total_h, 9)
  expect(Number(row?.[4])).toBeCloseTo(pair.changed.total_h, 9)
  expect(Number(row?.[7])).toBeCloseTo(pair.delta_h, 9)
  expect(row?.[9]).toBe(api.model_version)
  expect(row?.[10]).toBe(api.artifact_version)
  expect(JSON.parse(row?.[11] ?? "[]")).toEqual(api.changes)
  const numbers = JSON.parse(await readFile("../presentation/numbers.json", "utf8"))
  expect(numbers.baseline.value).toBeCloseTo(pair.baseline.total_h, 9)
  expect(numbers.frequency7.value).toBeCloseTo(pair.changed.total_h, 9)
  expect(numbers.gain7.value).toBeCloseTo(-pair.delta_h, 9)
  const passport = await readFile("../docs/submission/passport.md", "utf8")
  expect(passport).toContain("18,095")
  expect(passport).toContain("14,243")
  expect(passport).toContain("−3,852")
})
