import AxeBuilder from "@axe-core/playwright"
import { expect, type Page, test } from "@playwright/test"

const ROUTES = ["/", "/missing-page"]
const WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]

async function settle(page: Page): Promise<void> {
  await page.waitForFunction(() =>
    document
      .getAnimations()
      .filter((animation) => animation.effect?.getTiming().iterations !== Number.POSITIVE_INFINITY)
      .every((animation) => animation.playState !== "running"),
  )
}

async function audit(page: Page, route: string): Promise<void> {
  await page.goto(route)
  await expect(page.locator("#main h1")).toBeVisible()
  await settle(page)
  const result = await new AxeBuilder({ page }).withTags(WCAG_TAGS).analyze()
  const violations = result.violations.map((violation) => ({
    id: violation.id,
    impact: violation.impact,
    targets: violation.nodes.slice(0, 3).map((node) => node.target.join(" ")),
  }))
  expect(violations, route).toEqual([])
}

test("axe", async ({ page }) => {
  for (const route of ROUTES) {
    await audit(page, route)
    await expect(page.locator("html")).toHaveAttribute("lang", "ru")
  }
})
