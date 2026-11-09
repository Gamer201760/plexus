import { expect, type Locator, test } from "@playwright/test"
import mapMessages from "../src/shared/i18n/locales/ru/map.json" with { type: "json" }

const surface = "[data-map-surface]"

async function zoomOf(map: Locator): Promise<number> {
  return Number((await map.getAttribute("data-zoom")) ?? "0")
}

async function centerOf(map: Locator): Promise<string> {
  return (await map.getAttribute("data-center")) ?? ""
}

async function openMap(page: import("@playwright/test").Page): Promise<Locator> {
  await page.goto("/")
  const map = page.locator(surface)
  await expect(map).toBeVisible()
  await expect.poll(() => zoomOf(map)).toBeGreaterThan(0)
  return map
}

test("zoom control zooms in and reset returns home", async ({ page }) => {
  const map = await openMap(page)
  const home = await zoomOf(map)
  await page.getByRole("button", { name: mapMessages.zoomIn, exact: true }).click()
  await expect.poll(() => zoomOf(map)).toBeGreaterThan(home + 0.5)
  await page.getByRole("button", { name: mapMessages.reset, exact: true }).click()
  await expect.poll(async () => Math.abs((await zoomOf(map)) - home)).toBeLessThan(0.05)
})

test("wheel zooms into the map", async ({ page }) => {
  const map = await openMap(page)
  const home = await zoomOf(map)
  const box = await map.boundingBox()
  if (!box) throw new Error("Map is missing")
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2)
  await page.mouse.wheel(0, -400)
  await expect.poll(() => zoomOf(map)).toBeGreaterThan(home)
  expect(await page.evaluate(() => window.visualViewport?.scale)).toBe(1)
})

test("drag pans the map without selecting a region", async ({ page }) => {
  const map = await openMap(page)
  const before = await centerOf(map)
  const box = await map.boundingBox()
  if (!box) throw new Error("Map is missing")
  const x = box.x + box.width / 2
  const y = box.y + box.height / 2
  await page.mouse.move(x, y)
  await page.mouse.down()
  await page.mouse.move(x + 120, y + 60, { steps: 10 })
  await page.mouse.up()
  await expect.poll(() => centerOf(map)).not.toBe(before)
  expect(new URL(page.url()).searchParams.has("region")).toBe(false)
})

test("clicking a region selects it and the camera focuses", async ({ page }) => {
  const map = await openMap(page)
  const home = await zoomOf(map)
  const box = await map.boundingBox()
  if (!box) throw new Error("Map is missing")
  await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2)
  await expect.poll(() => new URL(page.url()).searchParams.has("region")).toBe(true)
  await expect.poll(() => zoomOf(map)).toBeGreaterThan(home)
})

test("keyboard zoom and reset are immediate with reduced motion", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" })
  const map = await openMap(page)
  const home = await zoomOf(map)
  await page.getByRole("button", { name: mapMessages.zoomIn, exact: true }).focus()
  await page.keyboard.press("Enter")
  await expect.poll(() => zoomOf(map)).toBeGreaterThan(home + 0.5)
  await page.getByRole("button", { name: mapMessages.reset, exact: true }).focus()
  await page.keyboard.press("Enter")
  await expect.poll(async () => Math.abs((await zoomOf(map)) - home)).toBeLessThan(0.05)
})

test("rapid top navigation stays responsive and leaves a rendered map", async ({ page }) => {
  await openMap(page)
  for (const path of ["/compare", "/sources", "/"]) {
    await page.locator(`header nav a[href^="${path}?"]`).click()
    await expect.poll(() => new URL(page.url()).pathname).toBe(path)
  }
  await expect(page.locator(surface)).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
})

test("attribution links to the tile provider", async ({ page }) => {
  const map = await openMap(page)
  const attribution = map.locator("..").getByRole("link", { name: mapMessages.attribution })
  await expect(attribution).toBeVisible()
  expect(await attribution.getAttribute("href")).toContain("copyright")
})
