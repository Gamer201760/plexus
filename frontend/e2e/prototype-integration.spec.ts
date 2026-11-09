import { expect, test } from "@playwright/test"
import calendar from "../src/shared/i18n/locales/ru/calendar.json" with { type: "json" }
import nav from "../src/shared/i18n/locales/ru/nav.json" with { type: "json" }
import sources from "../src/shared/i18n/locales/ru/sources.json" with { type: "json" }

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
  await page.getByRole("link", { name: nav.compare, exact: true }).click()
  await page.getByRole("link", { name: nav.sources, exact: true }).click()
  await expect(last).toHaveAttribute("aria-selected", "true")
  expect(new URL(page.url()).searchParams.get("season")).toBe("summer")
  const disclosure = page.getByRole("button", { name: sources.usage, exact: true }).first()
  await disclosure.click()
  await expect(disclosure).toHaveAttribute("aria-expanded", "true")
  await disclosure.click()
  await expect(disclosure).toHaveAttribute("aria-expanded", "false")
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
