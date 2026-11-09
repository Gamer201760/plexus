import { readFileSync } from "node:fs"
import { join } from "node:path"
import { FONT_PACKAGES, pickFontFaces } from "../exportTokens.ts"

export function embeddedFontFaces(frontendRoot: string): string {
  return FONT_PACKAGES.map((name) => {
    const packageDir = join(frontendRoot, "node_modules", ...name.split("/"))
    const faces = pickFontFaces(readFileSync(join(packageDir, "index.css"), "utf8"))
    return faces.files.reduce((css, file) => {
      const data = readFileSync(join(packageDir, "files", file)).toString("base64")
      return css.replaceAll(`url("fonts/${file}")`, `url("data:font/woff2;base64,${data}")`)
    }, faces.css)
  }).join("\n")
}

export function sansFamily(frontendRoot: string): string {
  const css = readFileSync(
    join(frontendRoot, "src", "shared", "styles", "tokens", "typography.css"),
    "utf8",
  )
  return /--font-sans:\s*([^;]+);/.exec(css)?.[1]?.replace(/\s+/g, " ").trim() ?? "sans-serif"
}
