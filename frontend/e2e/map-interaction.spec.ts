import { expect, type Locator, test } from "@playwright/test"
import mapMessages from "../src/shared/i18n/locales/ru/map.json" with { type: "json" }

const surface = "[data-map-surface]"
const home = { scale: 1, x: 0, y: 0 }
async function view(map: Locator): Promise<typeof home> {
  return JSON.parse((await map.getAttribute("data-view")) ?? "{}")
}

test("map wheel prevents page zoom and commits once per gesture", async ({ page }) => {
  await page.goto("/")
  const map = page.locator(surface)
  await expect(map).toBeVisible()
  const result = await map.evaluate(async (element) => {
    let commits = 0
    const observer = new MutationObserver((entries) => {
      commits += entries.length
    })
    observer.observe(element, { attributes: true, attributeFilter: ["data-view"] })
    const bounds = element.getBoundingClientRect()
    let prevented = true
    for (let i = 0; i < 12; i += 1) {
      const event = new WheelEvent("wheel", {
        deltaY: -20,
        ctrlKey: true,
        bubbles: true,
        cancelable: true,
        clientX: bounds.x + bounds.width / 2,
        clientY: bounds.y + bounds.height / 2,
      })
      element.dispatchEvent(event)
      prevented &&= event.defaultPrevented
      await new Promise(requestAnimationFrame)
    }
    const during = commits
    await new Promise((resolve) => setTimeout(resolve, 400))
    observer.disconnect()
    return { prevented, during, commits }
  })
  expect(result).toEqual({ prevented: true, during: 0, commits: 1 })
  expect((await view(map)).scale).toBeGreaterThan(1)
})

test("horizontal wheel pans without changing scale and reset works without a selection", async ({
  page,
}) => {
  await page.goto("/")
  const map = page.locator(surface)
  await expect(map).toBeVisible()
  const box = await map.boundingBox()
  if (!box) throw new Error("Map is missing")
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2)
  await page.mouse.wheel(0, -400)
  await page.waitForTimeout(400)
  const before = await view(map)
  await page.mouse.wheel(100, 0)
  await page.waitForTimeout(400)
  const after = await view(map)
  expect(after.scale).toBe(before.scale)
  expect(after.x).not.toBe(before.x)
  await page.getByRole("button", { name: mapMessages.reset, exact: true }).click()
  await expect.poll(() => view(map)).toEqual(home)
})

test("drag commits only on release and does not select a region", async ({ page }) => {
  await page.goto("/")
  const map = page.locator(surface)
  await expect(map).toBeVisible()
  const box = await map.boundingBox()
  if (!box) throw new Error("Map is missing")
  const x = box.x + box.width / 2,
    y = box.y + box.height / 2
  await page.mouse.move(x, y)
  const before = await view(map)
  await page.mouse.down()
  await page.mouse.move(x + 100, y + 50, { steps: 10 })
  expect(await view(map)).toEqual(before)
  await page.mouse.up()
  await expect.poll(() => view(map)).not.toEqual(before)
  expect(new URL(page.url()).searchParams.has("region")).toBe(false)
})

test("two-finger pinch zooms the map on mobile", async ({ page, context }) => {
  await page.setViewportSize({ width: 375, height: 812 })
  await page.goto("/")
  const map = page.locator(surface)
  await expect(map).toBeVisible()
  const box = await map.boundingBox()
  if (!box) throw new Error("Map is missing")
  const x = box.x + box.width / 2,
    y = box.y + box.height / 2
  const cdp = await context.newCDPSession(page)
  await cdp.send("Input.dispatchTouchEvent", {
    type: "touchStart",
    touchPoints: [
      { x: x - 30, y, id: 1 },
      { x: x + 30, y, id: 2 },
    ],
  })
  for (let i = 1; i <= 8; i += 1) {
    await cdp.send("Input.dispatchTouchEvent", {
      type: "touchMove",
      touchPoints: [
        { x: x - 30 - i * 6, y, id: 1 },
        { x: x + 30 + i * 6, y, id: 2 },
      ],
    })
  }
  await cdp.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] })
  await expect.poll(async () => (await view(map)).scale).toBeGreaterThan(1)
  expect(await page.evaluate(() => window.visualViewport?.scale)).toBe(1)
  expect(new URL(page.url()).searchParams.has("region")).toBe(false)
})

test("rapid top navigation stays responsive and leaves a rendered map", async ({ page }) => {
  await page.goto("/")
  await expect(page.locator(surface)).toBeVisible()
  for (const path of ["/compare", "/sources", "/"]) {
    await page.locator(`header nav a[href^="${path}?"]`).click()
    await expect.poll(() => new URL(page.url()).pathname).toBe(path)
  }
  await expect(page.locator(surface)).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
})

test("a wheel gesture interrupts flight at its visible position", async ({ page }) => {
  await page.goto("/")
  const map = page.locator(surface)
  await expect(map).toBeVisible()
  await page.getByRole("button", { name: mapMessages.zoomIn, exact: true }).click()
  await page.waitForTimeout(60)
  await map.evaluate((element) => {
    const rect = element.getBoundingClientRect()
    element.dispatchEvent(
      new WheelEvent("wheel", {
        deltaY: 0,
        bubbles: true,
        cancelable: true,
        clientX: rect.x + rect.width / 2,
        clientY: rect.y + rect.height / 2,
      }),
    )
  })
  await page.waitForTimeout(500)
  const scale = (await view(map)).scale
  expect(scale).toBeGreaterThan(1)
  expect(scale).toBeLessThan(1.6)
})

test("keyboard zoom and reset are immediate with reduced motion", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" })
  await page.goto("/")
  const map = page.locator(surface)
  await expect(map).toBeVisible()
  await page.getByRole("button", { name: mapMessages.zoomIn, exact: true }).focus()
  await page.keyboard.press("Enter")
  expect((await view(map)).scale).toBeCloseTo(1.6)
  await page.getByRole("button", { name: mapMessages.reset, exact: true }).focus()
  await page.keyboard.press("Enter")
  expect(await view(map)).toEqual(home)
})
