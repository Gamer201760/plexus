import { expect, test } from "@playwright/test"
import commonCopy from "../src/shared/i18n/locales/ru/common.json" with { type: "json" }
import pilotCopy from "../src/shared/i18n/locales/ru/pilot.json" with { type: "json" }

test("pilot recovers from unavailable API", async ({ page }) => {
  await page.route("**/api/v1/pilots/tuva", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ error: { code: "data_unavailable", message: "Pilot unavailable" } }),
    }),
  )
  await page.goto("/pilot")
  const retry = page.getByRole("button", { name: commonCopy.action.retry, exact: true })
  await expect(retry).toBeVisible()
  await page.unroute("**/api/v1/pilots/tuva")
  await retry.click()
  await expect(page.getByRole("button", { name: pilotCopy.calculate, exact: true })).toBeVisible()
})

test("desktop stand renders a long region name with external requests blocked", async ({
  page,
  request,
  baseURL,
}) => {
  const regions: { id: string; name: string }[] = await (
    await request.get("/api/v1/regions")
  ).json()
  const longest = [...regions].sort((a, b) => b.name.length - a.name.length)[0]
  expect(longest).toBeDefined()
  const blocked: string[] = []
  await page.route("**/*", (route) => {
    if (new URL(route.request().url()).origin === new URL(baseURL ?? "").origin)
      return route.continue()
    blocked.push(route.request().url())
    return route.abort()
  })
  await page.goto(`/map?metric=hansen&season=summer&region=${longest?.id}`)
  const title = page.getByText(longest?.name ?? "", { exact: true }).first()
  await expect(title).toBeVisible()
  const box = await title.boundingBox()
  expect(box).not.toBeNull()
  expect((box?.x ?? 0) + (box?.width ?? 0)).toBeLessThanOrEqual(1440)
  await page.evaluate(() => document.fonts.ready)
  expect(await page.evaluate(() => document.fonts.status)).toBe("loaded")
  expect(blocked).toEqual([])
})
