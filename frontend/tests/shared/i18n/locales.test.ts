import { readdirSync, readFileSync } from "node:fs"
import { join, resolve } from "node:path"
import { describe, expect, it } from "vitest"
import { NAMESPACES } from "@/shared/i18n/resources"

const LOCALES_DIR = resolve(process.cwd(), "src/shared/i18n/locales")
const PLURAL_SUFFIX = /_(zero|one|two|few|many|other)$/

type Tree = { readonly [key: string]: unknown }

function leafKeys(tree: Tree, prefix = ""): string[] {
  return Object.entries(tree).flatMap(([key, value]) =>
    typeof value === "object" && value !== null
      ? leafKeys(value as Tree, `${prefix}${key}.`)
      : [`${prefix}${key}`.replace(PLURAL_SUFFIX, "")],
  )
}

function leafValues(tree: Tree): string[] {
  return Object.values(tree).flatMap((value) =>
    typeof value === "object" && value !== null ? leafValues(value as Tree) : [String(value)],
  )
}

const read = (locale: string, file: string) =>
  JSON.parse(readFileSync(join(LOCALES_DIR, locale, file), "utf8")) as Tree
const filesOf = (locale: string) =>
  readdirSync(join(LOCALES_DIR, locale))
    .filter((file) => file.endsWith(".json"))
    .sort()

describe("dictionaries", () => {
  it("has only the russian dictionary", () => {
    expect(readdirSync(LOCALES_DIR)).toEqual(["ru"])
  })

  it("registers every namespace file in resources", () => {
    expect(filesOf("ru")).toEqual(NAMESPACES.map((namespace) => `${namespace}.json`).sort())
  })

  it.each(filesOf("ru"))("ru/%s is not empty", (file) => {
    const keys = leafKeys(read("ru", file))
    expect(keys.length).toBeGreaterThan(0)
  })

  it.each(filesOf("ru"))("ru/%s has no empty values and no internal identifiers", (file) => {
    const values = leafValues(read("ru", file))
    expect(values.filter((value) => value.trim() === "")).toEqual([])
    expect(values.filter((value) => /\b[a-z]+_[a-z_]+\b/.test(value))).toEqual([])
  })
})
