import copy from "@/shared/i18n/locales/ru/chat.json"

const metadataHeading = new RegExp(
  `^(?:#{1,6}\\s*)?(?:\\*\\*)?(?:${copy.normalization.metadata.join("|")})(?:\\*\\*)?\\s*[:：]`,
  "iu",
)
const scopeHeading = new RegExp(
  `^(?:#{1,6}\\s*)?(?:\\*\\*)?(?:${copy.normalization.scope.join("|")})(?:\\*\\*)?\\s*[:：]`,
  "iu",
)
const caveat = new RegExp(copy.normalization.caveats.join("|"), "iu")

function presentBlock(block: string): { text: string; details: string } {
  const trimmed = block.trim()
  if (metadataHeading.test(trimmed) && !caveat.test(trimmed)) {
    if (!scopeHeading.test(trimmed)) return { text: "", details: block }
    const sentences = block.split(/(?<=[.!?])\s+(?=\p{Lu})/u)
    return { text: sentences.slice(1).join(" "), details: sentences[0] ?? block }
  }
  return { text: block.replace(/^([ \t]*)[•●]\s+/gmu, "$1- "), details: "" }
}

export function presentMessage(text: string) {
  const pieces = text.replaceAll("\r\n", "\n").split(/(```[\s\S]*?(?:```|$)|~~~[\s\S]*?(?:~~~|$))/g)
  const blocks = pieces.flatMap((piece) =>
    /^(?:```|~~~)/u.test(piece)
      ? [{ text: piece, details: "" }]
      : piece.split(/\n\s*\n/u).map(presentBlock),
  )
  return {
    text: blocks
      .map((block) => block.text)
      .filter(Boolean)
      .join("\n\n")
      .trim(),
    details: blocks
      .map((block) => block.details)
      .filter(Boolean)
      .join("\n\n")
      .trim(),
  }
}
