import { readdirSync, writeFileSync } from "node:fs"
import { join, resolve } from "node:path"

const root = resolve(import.meta.dirname, "..")
const localesDir = join(root, "src", "shared", "i18n", "locales")
const target = join(root, "src", "shared", "i18n", "resources.ts")
const FIRST = ["common", "errors"]

const files = readdirSync(join(localesDir, "ru"))
  .filter((file) => file.endsWith(".json"))
  .map((file) => file.replace(/\.json$/, ""))
const namespaces = [
  ...FIRST.filter((name) => files.includes(name)),
  ...files.filter((name) => !FIRST.includes(name)).sort(),
]
const pascal = (name: string) =>
  name
    .split("-")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join("")

const imports = namespaces
  .map((name) => `import ru${pascal(name)} from "./locales/ru/${name}.json"`)
  .sort((left, right) => left.localeCompare(right))
const entries = namespaces.map((name) => `  "${name}": ru${pascal(name)},`).join("\n")

const text = `import type { Locale } from "./locale"
${imports.join("\n")}

export const NAMESPACES = [${namespaces.map((name) => `"${name}"`).join(", ")}] as const

export type Namespace = (typeof NAMESPACES)[number]

export const DEFAULT_NAMESPACE: Namespace = "common"

const ru = {
${entries}
}

export type Dictionary = typeof ru

export const resources = { ru } satisfies Record<Locale, Record<Namespace, object>>
`
writeFileSync(target, text)
process.stdout.write(`resources: ${namespaces.join(", ")}\n`)
