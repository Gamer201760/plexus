import { mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs"
import { join, resolve } from "node:path"
import { fileURLToPath } from "node:url"
import { chromium, type Page } from "@playwright/test"
import { embeddedFontFaces, sansFamily } from "./brand/fonts.ts"
import { type BadgeSpec, readContent } from "./readme/content.ts"
import {
  badgePage,
  bannerPage,
  buttonPage,
  footerPage,
  type PageInput,
  type ReadmeTheme,
} from "./readme/page.ts"
import { readTokenSources, themeColor } from "./tokenSources.ts"

type Variant = "light" | "dark"

interface Shot {
  readonly file: string
  readonly width: number
  readonly height: number
}

interface RowItem {
  readonly name: string
  readonly alt: string
  readonly href: string | undefined
  readonly shot: Shot
}

const frontendRoot = resolve(fileURLToPath(new URL("..", import.meta.url)))
const repoRoot = resolve(frontendRoot, "..")
const outDir = join(repoRoot, "docs", "readme")
const readmePath = join(repoRoot, "README.md")
const LINE_LIMIT = 660
const GAP = 6
const sources = readTokenSources(frontendRoot)
const content = readContent(repoRoot)
const BANNER = content.banner

function token(name: string): string {
  const color = themeColor(sources, "light", name)
  if (color === null) throw new Error(`token ${name} has no value`)
  return color
}

const THEMES: Readonly<Record<Variant, ReadmeTheme>> = {
  light: {
    text: token("--text-primary"),
    muted: token("--text-secondary"),
    label: token("--text-secondary"),
    labelSurface: token("--neutral-50"),
    valueSurface: token("--neutral-0"),
    border: token("--border-default"),
    accent: token("--action-primary"),
    onAccent: token("--action-primary-text"),
    warning: token("--text-warning"),
  },
  dark: {
    text: token("--neutral-50"),
    muted: token("--neutral-300"),
    label: token("--neutral-300"),
    labelSurface: token("--neutral-800"),
    valueSurface: token("--neutral-900"),
    border: token("--neutral-700"),
    accent: token("--blue-500"),
    onAccent: token("--neutral-0"),
    warning: token("--orange-2"),
  },
}

function wordmark(variant: Variant): string {
  return readFileSync(join(repoRoot, "docs", "brand", `wordmark-${variant}.svg`), "utf8")
}

async function shoot(page: Page, html: string, file: string): Promise<Shot> {
  await page.setContent(html)
  await page.evaluate(() => document.fonts.ready)
  const asset = page.locator("#asset")
  const box = await asset.boundingBox()
  if (box === null) throw new Error(`${file} has no box`)
  writeFileSync(join(outDir, file), await asset.screenshot({ omitBackground: true }))
  return { file, width: Math.round(box.width), height: Math.round(box.height) }
}

async function renderBoth(
  page: Page,
  name: string,
  build: (input: PageInput) => string,
  fonts: string,
  family: string,
): Promise<Shot> {
  let light: Shot | null = null
  for (const variant of ["light", "dark"] as const) {
    const input = { theme: THEMES[variant], fonts, family, wordmark: wordmark(variant) }
    const shot = await shoot(page, build(input), `${name}.${variant}.png`)
    if (variant === "light") light = shot
  }
  if (light === null) throw new Error(`${name} was not rendered`)
  return { ...light, file: `${name}.png` }
}

function picture(item: RowItem): string {
  const base = `docs/readme/${item.shot.file.replace(/\.png$/, "")}`
  const image = `<picture><source media="(prefers-color-scheme: dark)" srcset="${base}.dark.png"><img src="${base}.light.png" width="${item.shot.width}" height="${item.shot.height}" alt="${item.alt}"></picture>`
  return item.href === undefined ? image : `<a href="${item.href}">${image}</a>`
}

function lines(items: readonly RowItem[]): string {
  const rows: RowItem[][] = [[]]
  let used = 0
  for (const item of items) {
    const current = rows[rows.length - 1] ?? []
    if (current.length > 0 && used + GAP + item.shot.width > LINE_LIMIT) {
      rows.push([item])
      used = item.shot.width
    } else {
      current.push(item)
      used += (current.length > 1 ? GAP : 0) + item.shot.width
    }
  }
  return rows.map((row) => row.map(picture).join("\n")).join("\n<br>\n")
}

function replaceBlock(text: string, marker: string, content: string): string {
  const open = `<!-- readme:${marker} -->`
  const close = `<!-- /readme:${marker} -->`
  const start = text.indexOf(open)
  const end = text.indexOf(close)
  if (start === -1 || end === -1) throw new Error(`README.md has no ${marker} markers`)
  return `${text.slice(0, start + open.length)}\n${content}\n${text.slice(end)}`
}

function badgeAlt(badge: BadgeSpec): string {
  return badge.label === undefined ? badge.value : `${badge.label}: ${badge.value}`
}

mkdirSync(outDir, { recursive: true })
for (const file of readdirSync(outDir)) {
  if (/\.(light|dark)\.png$/.test(file)) rmSync(join(outDir, file))
}

const fonts = embeddedFontFaces(frontendRoot)
const family = sansFamily(frontendRoot)
const browser = await chromium.launch()
const page = await browser.newPage({ deviceScaleFactor: 2 })

const banner = await renderBoth(
  page,
  "banner",
  (input) => bannerPage(input, BANNER.promise, BANNER.note),
  fonts,
  family,
)
const footer = await renderBoth(page, "footer", (input) => footerPage(input), fonts, family)

const buttons: RowItem[] = []
for (const button of content.buttons) {
  const shot = await renderBoth(
    page,
    `button-${button.name}`,
    (input) => buttonPage(input, button),
    fonts,
    family,
  )
  buttons.push({ name: button.name, alt: button.label, href: button.href, shot })
}

async function badges(group: string, specs: readonly BadgeSpec[]): Promise<RowItem[]> {
  const items: RowItem[] = []
  for (const spec of specs) {
    const shot = await renderBoth(
      page,
      `${group}-${spec.name}`,
      (input) => badgePage(input, spec),
      fonts,
      family,
    )
    items.push({ name: spec.name, alt: badgeAlt(spec), href: spec.href, shot })
  }
  return items
}

const status = await badges("status", content.status)
const stack = await badges("stack", content.stack)
const nav = await badges("nav", content.nav)
await browser.close()

let readme = readFileSync(readmePath, "utf8")
readme = replaceBlock(
  readme,
  "banner",
  picture({ name: "banner", alt: `Plexus. ${BANNER.promise}`, href: undefined, shot: banner }),
)
readme = replaceBlock(readme, "buttons", lines(buttons))
readme = replaceBlock(readme, "status", lines(status))
readme = replaceBlock(readme, "stack", lines(stack))
readme = replaceBlock(readme, "nav", lines(nav))
readme = replaceBlock(
  readme,
  "footer",
  picture({ name: "footer", alt: "Plexus", href: undefined, shot: footer }),
)
writeFileSync(readmePath, readme)
process.stdout.write(`docs/readme: ${readdirSync(outDir).length} files, README.md rows updated\n`)
