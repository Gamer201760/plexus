import { describe, expect, it } from "vitest"
import { contrast, singleTheme } from "../../../scripts/checks/rules/css/themeTokens.ts"
import type { SourceFile } from "../../../scripts/checks/types.ts"

const tokens = (name: string, text: string): SourceFile => ({
  path: `src/shared/styles/tokens/${name}`,
  text,
})
const PALETTE = tokens(
  "palette.css",
  ":root { --white: #ffffff; --ink: #1a1a1e; --mist: #f6f6f7; --grey: #ececee; --blue: #3d5bd9; --pale: #b4b4bc; }",
)
const LIGHT = `--surface-base: var(--mist); --surface-raised: var(--white); --surface-raised-hover: color-mix(in oklab, var(--white), var(--ink) 4%); --surface-sunken: var(--grey); --surface-selected: var(--white); --text-primary: var(--ink); --text-disabled: var(--pale); --action-primary-text: var(--white); --action-primary: var(--blue); --action-primary-hover: var(--blue); --action-primary-press: var(--blue); --focus-ring: var(--blue);`
const semantic = (body: string, extra = "") => tokens("semantic.css", `:root { ${body} }\n${extra}`)

describe("single-theme", () => {
  it("passes a semantic layer defined once in :root", () => {
    expect(singleTheme.run([PALETTE, semantic(LIGHT)])).toEqual([])
  })

  it("reports a theme scope in semantic.css", () => {
    const messages = singleTheme
      .run([PALETTE, semantic(LIGHT, ':root[data-theme="dark"] { --text-primary: #fff; }')])
      .map((item) => item.message)
    expect(messages).toEqual(['theme scope :root[data-theme="dark"] is not allowed'])
  })

  it("reports a missing :root block", () => {
    const messages = singleTheme
      .run([tokens("semantic.css", `.x { ${LIGHT} }`)])
      .map((item) => item.message)
    expect(messages).toContain("no :root block")
  })

  it("reports theme selectors in other tokens and in components", () => {
    const files = [
      semantic(LIGHT),
      tokens("elevation.css", ':root[data-theme="dark"] { --shadow: none; }'),
      { path: "src/features/x/x.module.css", text: ':root[data-theme="dark"] .x { color: red; }' },
      { path: "src/features/x/x.ts", text: "const dark = root.dataset.theme\n" },
      {
        path: "src/features/y/y.module.css",
        text: "@media (prefers-color-scheme: dark) { .y { color: red; } }",
      },
    ]
    expect(singleTheme.run(files).map((item) => item.file)).toEqual([
      "src/shared/styles/tokens/elevation.css",
      "src/features/x/x.module.css",
      "src/features/y/y.module.css",
      "src/features/x/x.ts",
    ])
  })
})

describe("contrast", () => {
  it("passes readable pairs", () => {
    expect(contrast.run([PALETTE, semantic(LIGHT)])).toEqual([])
  })

  it("reports a text token below 4.5:1 and an unresolved pair", () => {
    const messages = contrast
      .run([PALETTE, semantic(`${LIGHT} --text-secondary: var(--pale);`)])
      .map((item) => item.message)
    expect(messages.some((message) => message.startsWith("light: --text-secondary"))).toBe(true)
    const broken = contrast.run([PALETTE, semantic(LIGHT.replace("--action-primary-text", "--x"))])
    expect(broken.map((item) => item.message)).toContain(
      "light: cannot resolve --action-primary-text on --action-primary",
    )
  })
})
