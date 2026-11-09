import { expect, test } from "@playwright/test"
import dataCopy from "../src/shared/i18n/locales/ru/data.json" with { type: "json" }
import mapCopy from "../src/shared/i18n/locales/ru/map.json" with { type: "json" }

test("national mode preserves coverage and navigation through real API", async ({ page }) => {
  await page.goto("/map?metric=hansen&season=summer&region=93000000&network_mode=road")
  await expect(page.getByText("3,84", { exact: true })).toBeVisible()
  await expect(page.getByText(/hansen-frequency-v2/)).toBeVisible()
  const mode = page.getByRole("combobox", { name: dataCopy.network.label })
  await mode.focus()
  await mode.press("Enter")
  const response = page.waitForResponse((item) =>
    item.url().includes("/api/v1/regions/93000000?") &&
    item.url().includes("network_mode=multimodal"),
  )
  await page.getByRole("option", { name: dataCopy.network.multimodal, exact: true }).click()
  const payload = await (await response).json()
  expect(payload.index_population_coverage).toBeGreaterThan(0)
  expect(payload.index_population_coverage).toBeLessThanOrEqual(1)
  expect(payload.index_model_version).toBe("hansen-frequency-v2")
  await expect(page).toHaveURL(/network_mode=multimodal/)
  await page.screenshot({ path: "test-results/national-index-desktop.png" })
  await page.getByRole("link", { name: mapCopy.selected.open, exact: true }).click()
  await expect(page).toHaveURL(/regions\/93000000\?.*network_mode=multimodal/)
})
