import { expect, test } from "@playwright/test"
import calendar from "../src/shared/i18n/locales/ru/calendar.json" with { type: "json" }
import data from "../src/shared/i18n/locales/ru/data.json" with { type: "json" }
import home from "../src/shared/i18n/locales/ru/home.json" with { type: "json" }
import nav from "../src/shared/i18n/locales/ru/nav.json" with { type: "json" }
import region from "../src/shared/i18n/locales/ru/region.json" with { type: "json" }
import sources from "../src/shared/i18n/locales/ru/sources.json" with { type: "json" }

test("home signals keep moving and respect reduced motion", async ({ page }) => {
  await page.goto("/")
  const signal = page.locator('[data-signal="0"]')
  await expect(page.locator("[data-signal]")).toHaveCount(3)
  const before = await signal.evaluate((node) => getComputedStyle(node).transform)
  await expect
    .poll(() => signal.evaluate((node) => getComputedStyle(node).transform))
    .not.toBe(before)
  expect(
    await page
      .locator("[data-signal]")
      .evaluateAll(
        (nodes) =>
          nodes.filter((node) =>
            node.getAnimations().some((animation) => animation.playState === "running"),
          ).length,
      ),
  ).toBe(3)
  await page.emulateMedia({ reducedMotion: "reduce" })
  await expect(signal).toHaveCSS("display", "none")
  await page.getByRole("link", { name: home.open }).click()
  await expect(page).toHaveURL(/\/map$/)
})

test("source topics support keyboard and preserve selection across navigation", async ({
  page,
}) => {
  await page.goto("/sources?season=summer")
  for (const name of Object.values(sources.topics)) {
    const tab = page.getByRole("tab", { name, exact: true })
    await tab.click()
    await expect(tab).toHaveAttribute("aria-selected", "true")
    await expect(page.locator("article").first()).toBeVisible()
  }
  const last = page.getByRole("tab", { name: sources.topics.seasons, exact: true })
  await last.focus()
  await page.keyboard.press("Home")
  await expect(
    page.getByRole("tab", { name: sources.topics.network, exact: true }),
  ).toHaveAttribute("aria-selected", "true")
  await page.keyboard.press("End")
  await expect(last).toHaveAttribute("aria-selected", "true")
  expect(
    await page
      .getByRole("tabpanel")
      .evaluate(
        (node) =>
          node.getAnimations().filter((animation) => animation.playState === "running").length,
      ),
  ).toBe(0)
  await page.getByRole("link", { name: nav.method, exact: true }).click()
  await page.getByRole("link", { name: nav.sources, exact: true }).click()
  await expect(last).toHaveAttribute("aria-selected", "true")
  expect(new URL(page.url()).searchParams.get("season")).toBe("summer")
  const disclosure = page.getByRole("button", { name: sources.usage, exact: true }).first()
  await disclosure.click()
  await expect(disclosure).toHaveAttribute("aria-expanded", "true")
  await disclosure.click()
  await expect(disclosure).toHaveAttribute("aria-expanded", "false")
})

test("region filtering and global search preserve the chosen season", async ({ page, request }) => {
  await page.goto("/regions?season=winter")
  const search = page.getByRole("searchbox", { name: region.table.search })
  await search.fill("zzzzzzz")
  await expect(page.getByText(region.notFound, { exact: true })).toBeVisible()
  await search.fill("")
  await expect(page.locator("tbody tr").first()).toBeVisible()
  await page.getByRole("radio", { name: data.season.summer, exact: true }).click()
  await expect(page).toHaveURL(/season=summer/)
  await page.locator("tbody tr a").first().click()
  await expect(page).toHaveURL(/\/regions\/\d+\?season=summer/)
  const response = await request.get("/api/v1/regions/71800000?season=summer")
  const target = await response.json()
  await page.getByRole("combobox", { name: nav.search.label }).fill(target.name.slice(0, 5))
  await page.getByRole("option").first().click()
  await expect(page).toHaveURL(/\/regions\/71800000\?season=summer/)
})

test("winter calendar compares actual route reports and discloses uncertain closure", async ({
  page,
}) => {
  await page.goto("/regions/71800000?section=winter-calendar&season=winter")
  const bars = page.locator('[data-previous="false"]')
  await expect(bars).toHaveCount(9)
  await page
    .locator("label")
    .filter({ has: page.getByRole("checkbox") })
    .click()
  await expect(page.getByRole("checkbox")).toBeChecked()
  await expect(page.locator('[data-previous="true"]').first()).toBeVisible()
  const route = bars.first().locator("xpath=ancestor::button")
  await route.click()
  await expect(route).toHaveAttribute("aria-expanded", "true")
  await expect(page.getByText(calendar.limit, { exact: true }).first()).toBeVisible()
  await expect(page.locator('[data-open="true"]').first()).toBeVisible()
})

test("method matrix selects an illustration and renders the formula", async ({ page }) => {
  await page.goto("/method")
  const cells = page.locator("button[aria-pressed]")
  await expect(cells).toHaveCount(49)
  await cells.first().click()
  await expect(cells.first()).toHaveAttribute("aria-pressed", "true")
  await expect(page.locator("math")).toBeVisible()
})
