import { expect, test } from "@playwright/test"
import copy from "../src/shared/i18n/locales/ru/pilot.json" with { type: "json" }

test("empty frequency explains and preserves the original value", async ({ page }) => {
  await page.goto("/pilot")
  const frequency = page.getByRole("textbox", { name: copy.frequency, exact: true }).first()
  await frequency.fill("")
  await expect(page.getByText(copy.emptyFrequency, { exact: false }).first()).toBeVisible()
  const response = page.waitForResponse("**/api/v1/pilots/tuva/evaluate")
  await page.getByRole("button", { name: copy.calculate, exact: true }).click()
  const calculated = await response
  expect(calculated.request().postDataJSON().changes[0].frequency_per_week).toBeUndefined()
  expect((await calculated.json()).pairs[0].changed.total_h).toBeCloseTo(18.0951, 3)
})
