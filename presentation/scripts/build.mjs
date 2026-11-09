import { readFileSync, readdirSync, mkdirSync, writeFileSync } from "node:fs"
import { resolve, dirname } from "node:path"
import { fileURLToPath } from "node:url"

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..")
const numbers = JSON.parse(readFileSync(resolve(root, "numbers.json"), "utf8"))
const files = readdirSync(resolve(root, "src/slides")).filter((name) => name.endsWith(".html")).sort()
if (files.length !== 7) throw new Error("Exactly seven defense slides are required")
let slides = files.map((name) => readFileSync(resolve(root, "src/slides", name), "utf8")).join("\n")
if (/data-(steps|s|at|until)=/.test(slides)) throw new Error("Hidden presentation steps are forbidden")
slides = slides.replace(/<span data-num="([^"]+)"><\/span>/g, (_, key) => {
  const record = numbers[key]
  if (!record || !record.source) throw new Error(`Missing evidence for ${key}`)
  const text = record.value === null ? "Пересчёт не завершён" : new Intl.NumberFormat("ru-RU", {
    maximumFractionDigits: record.digits ?? 0, minimumFractionDigits: record.digits ?? 0,
  }).format(record.value)
  return `<span data-num="${key}">${text}</span>`
})
slides = slides.replace(/src="assets\/([^"]+)"/g, (_, name) => {
  const type = name.endsWith(".svg") ? "image/svg+xml" : "image/png"
  return `src="data:${type};base64,${readFileSync(resolve(root, "assets", name)).toString("base64")}"`
})
const tokensPath = resolve(root, "src/core/css/tokens.css")
const tokens = readFileSync(tokensPath, "utf8").replace(/\s+/g, " ")
writeFileSync(tokensPath, `${tokens}\n`)
const inlined = tokens.replace(/url\("fonts\/([^"]+)"\)/g, (_, name) =>
  `url("data:font/woff2;base64,${readFileSync(resolve(root, "src/core/css/fonts", name)).toString("base64")}")`)
const styles = `${inlined}\n${readFileSync(resolve(root, "src/core/css/deck.css"), "utf8")}`
const script = readFileSync(resolve(root, "src/engine.js"), "utf8")
const html = readFileSync(resolve(root, "src/shell.html"), "utf8")
  .replace("__STYLES__", styles).replace("__SLIDES__", slides).replace("__SCRIPT__", script)
if (/__STYLES__|__SLIDES__|__SCRIPT__/.test(html)) throw new Error("Unresolved deck template")
mkdirSync(resolve(root, "dist"), { recursive: true })
writeFileSync(resolve(root, "dist/deck.html"), html)
console.log(`Built ${files.length} slides into self-contained dist/deck.html`)
