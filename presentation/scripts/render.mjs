import { readFileSync, writeFileSync, mkdirSync, copyFileSync } from "node:fs"
import { dirname, resolve } from "node:path"
import { fileURLToPath, pathToFileURL } from "node:url"
import { chromium } from "../../frontend/node_modules/@playwright/test/index.mjs"

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..")
const repository = resolve(root, "..")
const mode = process.argv[2] ?? "shots"
const output = resolve(repository, "docs/submission")
mkdirSync(output, { recursive: true })
const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1 })
const errors = []
page.on("pageerror", (error) => errors.push(error.message))
const url = pathToFileURL(resolve(root, "dist/deck.html")).href
if (mode === "shots") {
  mkdirSync(resolve(root, "shots"), { recursive: true })
  for (let slide = 1; slide <= 7; slide += 1) {
    await page.goto(`${url}?static#${slide}`)
    await page.evaluate(() => document.fonts.ready)
    const overflow = await page.locator(".slide:not([hidden])").evaluate((element) =>
      [...element.querySelectorAll("h1,h2,p,table,figure,li")].some((child) => {
        const box = child.getBoundingClientRect()
        const frame = element.getBoundingClientRect()
        return box.right > frame.right + 1 || box.bottom > frame.bottom - 45
      }))
    if (overflow) throw new Error(`Slide ${slide} overflows`)
    await page.screenshot({ path: resolve(root, `shots/${String(slide).padStart(2, "0")}.png`) })
  }
} else {
  if (mode === "final") {
    const numbers = JSON.parse(readFileSync(resolve(root, "numbers.json"), "utf8"))
    if (Object.values(numbers).some((record) => record.value === null)) throw new Error("Unverified deck numbers remain")
  }
  await page.goto(`${url}?print`)
  await page.evaluate(() => document.fonts.ready)
  await page.pdf({ path: resolve(output, "plexus-deck.pdf"), width: "1600px", height: "900px", printBackground: true, preferCSSPageSize: true })
  copyFileSync(resolve(root, "dist/deck.html"), resolve(output, "plexus-deck.html"))
  const tokens = readFileSync(resolve(root, "src/core/css/tokens.css"), "utf8").replace(/url\("fonts\/([^"]+)"\)/g,
    (_, file) => `url("data:font/woff2;base64,${readFileSync(resolve(root, "src/core/css/fonts", file)).toString("base64")}")`)
  const escaped = (value) => value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
  function inline(text) {
    return escaped(text).replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
  }
  function markdown(text) {
    return text.split(/\n\s*\n/).map((block) => {
      if (block.trim() === "[→]") return ""
      if (block.startsWith("|")) {
        const lines = block.trim().split("\n").filter((line) => !/^\|[ :|-]+\|$/.test(line))
        return `<table>${lines.map((line, index) => `<tr>${line.split("|").slice(1, -1).map((cell) => `<${index === 0 ? "th" : "td"}>${inline(cell.trim())}</${index === 0 ? "th" : "td"}>`).join("")}</tr>`).join("")}</table>`
      }
      const heading = block.match(/^(#{1,3}) (.+)$/s)
      if (heading) return `<h${heading[1].length}>${inline(heading[2])}</h${heading[1].length}>`
      return `<p>${inline(block).replaceAll("\n", " ")}</p>`
    }).join("\n")
  }
  const css = `${tokens}\n@page{size:A4;margin:16mm 18mm}body{font-family:var(--font-sans);font-size:10.3pt;line-height:1.35;color:var(--text-primary);margin:0}h1{font-size:22pt;line-height:1.1;margin:0 0 12pt}h2{font-size:12.5pt;line-height:1.15;margin:13pt 0 6pt}p{margin:0 0 7pt}table{width:100%;border-collapse:collapse;font-size:9.5pt;margin:8pt 0}th,td{padding:5pt;border-bottom:1px solid var(--border-subtle);text-align:left}a{color:var(--action-primary)}code{font-size:9pt}.paper-page{break-after:page}.paper-page:last-child{break-after:auto}`
  const passport = readFileSync(resolve(output, "passport.md"), "utf8")
  const split = passport.indexOf("## Проверенный результат пилота")
  const passportBody = `<section class="paper-page">${markdown(passport.slice(0, split))}</section><section class="paper-page">${markdown(passport.slice(split))}</section>`
  const passportHtml = `<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>Паспорт Plexus</title><style>${css}</style></head><body>${passportBody}</body></html>`
  writeFileSync(resolve(output, "passport.html"), passportHtml)
  await page.setContent(passportHtml)
  await page.evaluate(() => document.fonts.ready)
  await page.pdf({ path: resolve(output, "plexus-passport.pdf"), format: "A4", printBackground: true, preferCSSPageSize: true })
  const speech = readFileSync(resolve(root, "SPEECH.md"), "utf8")
  const speechHtml = `<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>Речь Plexus</title><style>${css}</style></head><body>${markdown(speech)}</body></html>`
  await page.setContent(speechHtml)
  await page.evaluate(() => document.fonts.ready)
  await page.pdf({ path: resolve(output, "plexus-speech.pdf"), format: "A4", printBackground: true, preferCSSPageSize: true })
  copyFileSync(resolve(root, "SPEECH.md"), resolve(output, "speech.md"))
}
await browser.close()
if (errors.length) throw new Error(errors.join("\n"))
console.log(`Rendered ${mode} with no browser errors`)
