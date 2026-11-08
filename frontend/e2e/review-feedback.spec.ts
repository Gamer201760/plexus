import { expect, test } from "@playwright/test"
import region from "../src/shared/i18n/locales/ru/region.json" with { type: "json" }
import sources from "../src/shared/i18n/locales/ru/sources.json" with { type: "json" }

test("source tab underline stays under the selected label", async ({ page }) => {
  await page.goto("/sources")
  for (const name of [sources.topics.seasons, sources.topics.network, sources.topics.economy]) {
    const tab = page.getByRole("tab", { name, exact: true })
    await tab.click()
    await expect(tab).toHaveAttribute("aria-selected", "true")
    const travelling = await page
      .getByRole("tablist")
      .evaluate((list) =>
        list
          .getAnimations({ subtree: true })
          .some(
            (animation) =>
              animation.effect instanceof KeyframeEffect &&
              animation.effect.getKeyframes().some((frame) => frame.clipPath !== undefined),
          ),
      )
    expect(travelling).toBe(false)
  }
})

test("method readout follows hover and keyboard focus", async ({ page }) => {
  await page.goto("/method")
  const cells = page.locator("button[aria-pressed]")
  await expect(cells).toHaveCount(49)
  await cells.first().hover()
  await expect(cells.first()).toHaveAttribute("aria-pressed", "true")
  await expect(
    page
      .locator('[aria-live="polite"]')
      .filter({ hasText: (await cells.first().getAttribute("aria-label")) ?? "" }),
  ).toBeVisible()
  await cells.last().focus()
  await expect(cells.last()).toHaveAttribute("aria-pressed", "true")
})

test("region page wheel reaches the end through the settlement table", async ({ page }) => {
  await page.goto("/regions/71800000?season=winter")
  await page.getByRole("button", { name: region.settlements.title, exact: true }).click()
  const table = page.getByRole("table", { name: region.settlements.title })
  await expect(table).toBeVisible()
  await table.scrollIntoViewIfNeeded()
  const box = await table.boundingBox()
  if (!box) throw new Error("Table is missing")
  const before = await page.evaluate(() => scrollY)
  await page.mouse.move(box.x + box.width / 2, Math.min(700, Math.max(200, box.y + 100)))
  await page.mouse.wheel(0, 700)
  await expect.poll(() => page.evaluate(() => scrollY)).toBeGreaterThan(before)
  await page.mouse.wheel(0, 700)
  await expect
    .poll(() => page.evaluate(() => document.documentElement.scrollHeight - innerHeight - scrollY))
    .toBeLessThan(2)
})

test("selected map region replaces the national ranking with its routes", async ({
  page,
  request,
}) => {
  const response = await request.get("/api/v1/regions/71800000/links?season=winter")
  const links = await response.json()
  await page.goto("/map?region=71800000&season=winter")
  await expect(page.locator("aside ol")).toHaveCount(0)
  await expect(
    page.locator("aside").getByText(links[0].from.name, { exact: true }).first(),
  ).toBeVisible()
  await expect(
    page.locator("aside").getByText(links[0].to.name, { exact: true }).first(),
  ).toBeVisible()
  await expect(page.locator("aside [data-link-id]")).toHaveCount(links.length)
})
