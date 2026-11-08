import { mkdirSync } from "node:fs"
import { join, resolve } from "node:path"
import { fileURLToPath } from "node:url"
import { chromium } from "@playwright/test"

interface HeroShot {
  readonly file: string
  readonly path: string
}

const SHOTS: readonly HeroShot[] = [
  { file: "hero-map.png", path: "/?region=04000000" },
  { file: "hero-region.png", path: "/regions/93000000" },
]

const repoRoot = resolve(fileURLToPath(new URL("../..", import.meta.url)))
const outDir = join(repoRoot, "docs", "readme")
const base = (process.env.APP_URL ?? "http://127.0.0.1:5173").replace(/\/$/, "")

mkdirSync(outDir, { recursive: true })
const browser = await chromium.launch()
const page = await browser.newPage({
  viewport: { width: 1440, height: 900 },
  deviceScaleFactor: 2,
  reducedMotion: "reduce",
})
for (const shot of SHOTS) {
  const response = await page.goto(`${base}${shot.path}`)
  if (response === null || !response.ok()) throw new Error(`${base}${shot.path} did not open`)
  await page.waitForLoadState("networkidle")
  await page.waitForTimeout(800)
  await page.screenshot({ path: join(outDir, shot.file) })
}
await browser.close()
process.stdout.write(`docs/readme: ${SHOTS.map((shot) => shot.file).join(", ")} from ${base}\n`)
