import { expect, test } from "@playwright/test"

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
  await page.goto(`/?metric=hansen&season=summer&region=${longest?.id}`)
  const title = page.getByText(longest?.name ?? "", { exact: true }).first()
  await expect(title).toBeVisible()
  const box = await title.boundingBox()
  expect(box).not.toBeNull()
  expect((box?.x ?? 0) + (box?.width ?? 0)).toBeLessThanOrEqual(1440)
  await page.evaluate(() => document.fonts.ready)
  expect(await page.evaluate(() => document.fonts.status)).toBe("loaded")
  expect(blocked).toEqual([])
})
