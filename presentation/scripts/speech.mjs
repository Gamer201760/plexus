import { createHash } from "node:crypto"
import { readFileSync, readdirSync, writeFileSync } from "node:fs"
import { dirname, resolve } from "node:path"
import { fileURLToPath } from "node:url"

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..")
const files = readdirSync(resolve(root, "src/slides")).filter((file) => file.endsWith(".html")).sort()
const speech = readFileSync(resolve(root, "SPEECH.md"), "utf8")
const sections = [...speech.matchAll(/^## \d+\. .+?\[([^\]]+)\] (\d+):(\d+)\s*\n([\s\S]*?)(?=^## |$(?![\s\S]))/gm)]
if (sections.length !== files.length) throw new Error("Speech must have one section for every slide")
let duration = 0
let words = 0
const fingerprint = createHash("sha256")
const rows = files.map((file, index) => {
  const html = readFileSync(resolve(root, "src/slides", file), "utf8")
  const id = html.match(/id="([^"]+)"/)?.[1]
  const seconds = Number(html.match(/data-time="(\d+)"/)?.[1])
  const section = sections[index]
  if (!section || section[1] !== id) throw new Error(`Speech order mismatch: ${file}`)
  const sectionSeconds = Number(section[2]) * 60 + Number(section[3])
  if (sectionSeconds !== seconds) throw new Error(`Speech timing mismatch: ${id}`)
  const text = section[4].replaceAll("[→]", "").trim()
  const count = text.split(/\s+/u).length
  if (count / (125 / 60) > seconds + 3) throw new Error(`Speech exceeds time for ${id}: ${count} words / ${seconds}s`)
  if ((section[4].match(/\[→\]/g) ?? []).length !== 1) throw new Error(`One slide key press required for ${id}`)
  if (/\{\{|\[NEED|\[N\]/.test(text)) throw new Error(`Unresolved speech marker: ${id}`)
  duration += seconds
  words += count
  fingerprint.update(html)
  return { id, seconds, words: count }
})
fingerprint.update(readFileSync(resolve(root, "numbers.json")))
fingerprint.update(speech)
const sha256 = fingerprint.digest("hex")
if (duration > 280 || words / (125 / 60) > 280) throw new Error("Speech exceeds the 5-minute slot with reserve")
const lock = { sha256, duration_s: duration, words, estimated_spoken_s: words / (125 / 60), slides: rows }
if (process.argv[2] === "sync") writeFileSync(resolve(root, "speech.lock.json"), `${JSON.stringify(lock, null, 2)}\n`)
else {
  const previous = JSON.parse(readFileSync(resolve(root, "speech.lock.json"), "utf8"))
  if (previous.sha256 !== sha256) throw new Error("Slides or speech changed: review them, then run speech:sync")
}
console.log(JSON.stringify(lock, null, 2))
