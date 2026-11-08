import { expect, test } from "@playwright/test"
import { mainlandBox } from "../src/entities/region/russia-map/map-shapes"

const mapSelector = '[data-map-surface], svg[role="img"]'

test("map can be dragged immediately after opening", async ({ page }) => {
  await page.goto("/map")
  const map = page.locator(mapSelector).first()
  await expect(map).toBeVisible()
  await page.waitForTimeout(500)
  const read = () =>
    map.evaluate(
      (element) =>
        element.getAttribute("data-view") ?? element.querySelector("g")?.getAttribute("style"),
    )
  const before = await read()
  const box = await map.boundingBox()
  if (!box) throw new Error("Map is missing")
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2)
  await page.mouse.down()
  await page.mouse.move(box.x + box.width / 2 + 140, box.y + box.height / 2 + 70, { steps: 15 })
  await page.mouse.up()
  await expect.poll(read).not.toBe(before)
})

test("selecting Arkhangelsk preserves the atlas camera", async ({ page }) => {
  await page.goto("/map?region=11000000")
  const map = page.locator(mapSelector).first()
  await expect(map).toBeVisible()
  await expect(map.locator('[data-region-id="11000000"]')).toBeAttached()
  const view = JSON.parse((await map.getAttribute("data-view")) ?? "{}")
  expect(view).toEqual({ scale: 1, x: 0, y: 0 })
})

test("gestures move the rendered stage and keep geometry until release", async ({ page }) => {
  await page.goto("/map?region=11000000")
  const map = page.locator("[data-map-surface]")
  const stage = map.locator("[data-map-stage]")
  const path = map.locator('[data-region-id="11000000"]')
  await expect(path).toBeAttached()
  await page.waitForTimeout(500)
  const before = await path.getAttribute("d")
  const during = await map.evaluate(async (element) => {
    let swaps = 0
    const observer = new MutationObserver((entries) => {
      swaps += entries.length
    })
    observer.observe(element, { attributes: true, attributeFilter: ["d"], subtree: true })
    const rect = element.getBoundingClientRect()
    for (let i = 0; i < 6; i += 1) {
      element.dispatchEvent(
        new WheelEvent("wheel", {
          deltaY: -16,
          bubbles: true,
          cancelable: true,
          clientX: rect.x + rect.width / 2,
          clientY: rect.y + rect.height / 2,
        }),
      )
      await new Promise(requestAnimationFrame)
    }
    observer.disconnect()
    const layer = element.querySelector("[data-map-stage]")
    return { swaps, transform: layer instanceof HTMLElement ? layer.style.transform : "" }
  })
  expect(during.swaps).toBe(0)
  expect(during.transform).toContain("scale(")
  await expect
    .poll(() => stage.evaluate((element) => (element as HTMLElement).style.transform))
    .toBe("")
  expect(await path.getAttribute("d")).toBe(before)
})

test("visible geometry and hit testing place Arkhangelsk at the same coordinates", async ({
  page,
  request,
}) => {
  const response = await request.get("/api/v1/geo/regions")
  const regions = (await response.json()).regions
  const region = regions.find((entry: { id: string }) => entry.id === "11000000")
  const box = mainlandBox(region.path)
  if (!box) throw new Error("Mainland is missing")
  await page.goto("/map")
  const map = page.locator("[data-map-surface]")
  await expect(map).toBeVisible()
  const target = await map.evaluate((element, box) => {
    const rect = element.getBoundingClientRect()
    const k = Math.max(1000 / rect.width, 620 / rect.height)
    return {
      x: rect.x + (rect.width - 1000 / k) / 2 + (box.x + box.width / 2) / k,
      y: rect.y + (rect.height - 620 / k) / 2 + (box.y + box.height / 2) / k,
    }
  }, box)
  await page.mouse.click(target.x, target.y)
  await expect(page).toHaveURL(/region=11000000/)
  await page.waitForTimeout(400)
  const offset = await map.locator('[data-region-id="11000000"]').evaluate((path, box) => {
    if (!(path instanceof SVGPathElement)) throw new Error("Region is missing")
    const matrix = path.getScreenCTM()
    const surface = path.closest("[data-map-surface]")?.getBoundingClientRect()
    if (!matrix || !surface) throw new Error("Map matrix is missing")
    const point = new DOMPoint(box.x + box.width / 2, box.y + box.height / 2).matrixTransform(
      matrix,
    )
    return [point.x, point.y]
  }, box)
  expect(Math.abs((offset[0] ?? 0) - target.x)).toBeLessThan(3)
  expect(Math.abs((offset[1] ?? 0) - target.y)).toBeLessThan(3)
})
